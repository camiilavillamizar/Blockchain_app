from node_server.models.Blockchain import Blockchain
from node_server.models.Blockchain.Block import Block
from node_server.models.Blockchain.Block.Transaction import Transaction
from flask import Flask, request
import jsons
import time
import requests
from copy import copy
from threading import Lock


def create_app():
    app = Flask(__name__)

    # the node's copy of blockchain
    blockchain = Blockchain()
    blockchain.create_genesis_block()
    # the blockchain's lock
    bloq_lock = Lock()

    # the address to other participating members of the network
    peers = set()
    # the peer list's lock
    peer_lock = Lock()

    # endpoint to submit a new transaction. This will be used by
    # our application to add new data (posts) to the blockchain
    @app.route('/new_transaction', methods=['POST'])
    def new_transaction():
        print(request.get_json())
        blockchain.add_new_transaction(Transaction.from_json(request.get_json()))
        return "Success", 201

    # endpoint to return the node's copy of the chain.
    # Our application will be using this endpoint to query
    # all the posts to display.
    @app.route('/chain', methods=['GET'])
    def get_chain():
        chain_data = []
        for block in blockchain.chain:
            chain_data.append(block)
        return jsons.dumps({"length": len(chain_data),
                           "chain": chain_data,
                           "peers": list(peers)})

    # endpoint to request the node to mine the unconfirmed
    # transactions (if any). We'll be using it to initiate
    # a command to mine from our application itself.
    @app.route('/mine', methods=['GET'])
    def mine_unconfirmed_transactions():
        nonlocal blockchain
        chain_length = len(blockchain.chain)
        consensus()
        if chain_length == len(blockchain.chain):
            pending = copy(blockchain.unconfirmed_transactions)
            result = blockchain.mine()
            if result:
                msg = copy(result[0])
                msg.hash = result[1]
                msg.own = True
                msg.pending_tx = pending
                requests.post("{}add_block".format(request.host_url),
                              headers={'Content-Type': "application/json"},
                              data=jsons.dumps(msg.__dict__, sort_keys=True))
                return "El bloque se ha enviado para inspección.", 202
            return "No hay transacciones por minar."

        else:
            print("actualizando cadena")
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
            peer_lock.acquire()
            try:
                print("error en register_node")
                peers.add(node_address)
            finally:
                peer_lock.release()
            # enviar una orden de registro a todos los demás nodos
            for node in [x for x in peers if x is not node_address]:
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

        data = {"node_address": request.host_url}
        headers = {'Content-Type': "application/json"}

        # Make a request to register with remote node and obtain information
        response = requests.post(node_address + "/register_node",
                                 data=jsons.dumps(data), headers=headers)

        if response.status_code == 200:
            nonlocal blockchain
            nonlocal peers
            # update chain and the peers
            chain_dump = response.json()['chain']
            bloq_lock.acquire()
            try:
                blockchain = create_chain_from_dump(chain_dump)
            finally:
                bloq_lock.release()

            # agrega el nodo con el que nos registramos, sus peers, y nos
            # eliminamos a nosotros mismos
            peer_lock.acquire()
            try:
                print("error en register_with")
                peers.update([node_address + "/"])
                peers.update(response.json()['peers'])
                peers.remove(request.host_url)
            finally:
                peer_lock.release()

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
        nonlocal peers
        peer = request.get_json()["node_address"]
        print(peer)
        print(peers)
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
                          json={'node_address': request.host_url})
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
        except KeyError:
            pending_tx = []
            print("no pending transactions found")
        proof = block_data.pop("hash")

        block = Block.from_json(block_data)

        # pedimos acceso a la cadena y esperamos a que la liberen
        bloq_lock.acquire()
        try:
            added = blockchain.add_block(block, proof)
        finally:
            bloq_lock.release()

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
                requests.get("{}mine".format(request.host_url))
                return "volviendo a minar, actualice pronto.", 202

        if not added:
            return "The block was discarded by the node", 400

        print("bloque externo fue añadido a la cadena.")
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
        nonlocal blockchain

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
                          data=jsons.dumps(block.__dict__, sort_keys=True),
                          headers=headers)

    return app


# Uncomment this line if you want to specify the port number in the code
# app.run(debug=True, port=8000)