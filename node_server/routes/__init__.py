from node_server.models import Blockchain, Transaction, Block, Content
from node_server.functions import saving_password, authentication
from flask import request, jsonify
from flask import current_app as app
import jsons
import time
import requests
from copy import copy



# the node's copy of blockchain
blockchain = Blockchain()
blockchain.create_genesis_block()

# the address to other participating members of the network
peers = set()

# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain

@app.route('/check_login', methods=['POST'])
def check_login():
    tx_data = request.get_json()
    message = authentication(tx_data)

    return message



@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()

    if tx_data['type'] == 'inscription':
        message = saving_password(tx_data) 
        tx_data.pop('password')

        if (message != True):
            return message

    blockchain.add_new_transaction(Transaction.from_json(tx_data))
    return "Success", 201

# endpoint to return the node's copy of the chain.
# Our application will be using this endpoint to query
# all the posts to display.


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.serialize)
    return jsonify({"length": len(chain_data),
                    "chain": chain_data,
                    "peers": list(peers)})

# endpoint to request the node to mine the unconfirmed
# transactions (if any). We'll be using it to initiate
# a command to mine from our application itself.


@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    global blockchain
    chain_length = len(blockchain.chain)
    consensus()
    if chain_length == len(blockchain.chain):
        pending = copy(blockchain.unconfirmed_transactions)
        result = blockchain.mine()
        if result:
            msg = copy(result[0].serialize)
            msg['hash'] = result[1]
            msg['own'] = True
            msg['pending_tx'] = pending
            requests.post("{}add_block".format('http://localhost:8000/'),
                          headers={'Content-Type': "application/json"},
                          data=jsons.dumps(msg, sort_keys=True))
            return "El bloque se ha enviado para inspección.", 202
        return "No hay transacciones por minar."

    else:
        dump = requests.get('{}chain'.format(next(iter(peers))))
        blockchain = create_chain_from_dump(dump.json()['chain'])
        mine_unconfirmed_transactions()

# endpoint to add new peers to the network.


@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    if node_address not in peers:
        peers.add(node_address)
        # enviar una orden de registro a todos los demás nodos
        for node in peers:
            requests.post("{}register_node".format(node),
                          json={'node_address': node_address})

    # Return the consensus blockchain to the newly registered node
    # so that he can sync
    return get_chain()


@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    """
    Internally calls the `register_node` endpoint to
    register current node with the node specified in the
    request, and sync the blockchain as well as peer data.
    """
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": 'http://localhost:8000/'}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remote node and obtain information
    response = requests.post(node_address + "/register_node",
                             data=jsons.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        global peers
        # update chain and the peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)

        # agrega el nodo con el que nos registramos, sus peers, y nos
        # eliminamos a nosotros mismos
        peers.update([node_address + "/"])
        peers.update(response.json()['peers'])
        peers.remove('http://localhost:8000/')

        return "Registration successful", 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code


def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue  # skip genesis block
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["datetime"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        proof = block_data['hash']
        added = generated_blockchain.add_block(block, proof)
        if not added:
            raise Exception("The chain dump is tampered!!")
    return generated_blockchain


@app.route('/remove_node', methods=['POST'])
def broadcast_remove_block():
    """ elimina el nodo dado y le envía la misma orden
    a todos los nodos enlazados. """
    global peers
    peer = request.get_json()["node_address"]
    if peer in peers:
        peers.remove(peer)
    return "eliminado con éxito."


def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug server')
    func()


@app.route('/leave')
def leave_network():
    """ le ordena al nodo abandonar la red, lo que hace anunciándose. """
    for peer in peers:
        requests.post('{}remove_node'.format(peer),
                      json={'node_address': 'http://localhost:8000/'})
    shutdown()
    return "Me han eliminado con éxito de la red."

# endpoint to add a block mined by someone else to
# the node's chain. The block is first verified by the node
# and then added to the chain.


@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    """ esta función recibe dos tipos de requests: los del mismo
    nodo, y los de los demás. los del mismo nodo se identifican por
    el bit 'own' del mensaje. estos reciben un tratamiento especial:
    si son aceptados por la cadena, se reenvían al resto de la red.
    si no, se repite la operación de minado, con los pending requests
    que le hagan falta."""
    # extract the special bits before creating the block
    block_data = request.get_json()
    own = block_data.pop("own")
    try:
        pending_tx = block_data.pop("pending_tx")
    except KeyError as e:
        pending_tx = []
    proof = block_data.pop("hash")


    block = Block.from_json(block_data)
    added = blockchain.add_block(block, proof)

    # si es nuestro propio bloque...
    if own:
        # ...y fue añadido, reenviar a los demás.
        if added:
            # se eliminan las transacciones que fueron minadas
            blockchain.unconfirmed_transactions = [
                x for x in blockchain.unconfirmed_transactions
                if x not in pending_tx]
            fwd = copy(block)
            fwd.hash = proof
            fwd.own = False
            announce_new_block(fwd)
            return "New block has been mined.", 201
        # ...de lo contrario, volver a minar.
        else:
            for tx in pending_tx:
                blockchain.unconfirmed_transactions.insert(0, tx)
            requests.get("{}mine".format('http://localhost:8000/'))
            return "volviendo a minar, actualice pronto.", 202

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201

# endpoint to query unconfirmed transactions


@app.route('/pending_tx')
def get_pending_tx():
    return jsons.dumps(blockchain.unconfirmed_transactions)


def consensus():
    """
    Our naive consnsus algorithm. If a longer valid chain is
    found, our chain is replaced with it.
    """
    global blockchain

    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = requests.get('{}chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False


def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined.
    Other blocks can simply verify the proof of work and add it to their
    respective chains.
    """
    for peer in peers:
        url = "{}add_block".format(peer)
        headers = {'Content-Type': "application/json"}
        requests.post(url,
                      data=jsons.dumps(block.serialize, sort_keys=True),
                      headers=headers)
