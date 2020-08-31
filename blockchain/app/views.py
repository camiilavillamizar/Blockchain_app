from datetime import datetime
import json
import os

import requests
from flask import render_template, redirect, request

from app import app

# The node with which our application interacts, there can be multiple
# such nodes as well.
RUNTIME_ENV = os.environ.get('RUNTIME_ENV')
CONNECTED_NODE_ADDRESS = os.environ.get('CONNECTED_NODE_ADDRESS') if RUNTIME_ENV =='DOCKER_ENVIRONMENT'  else "http://127.0.0.1:8000"


posts = []
stamplist =[]

def fetch_posts():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        chain = json.loads(response.content)
        global stamplist
        # filename = 'logs/tx.json'
        try:
            txwrite = open('logs/tx.json', 'r+')
        except:
            open('logs/tx.json', 'x')
            txwrite = open('logs/tx.json', 'r+')

        try:
            data = json.load(txwrite)

            for block in chain["chain"]:
                for tx in block["transactions"]:
                    tx["hash"] = block["previous_hash"]
                    if tx["datetime"] not in stamplist:
                        data.append(tx)
                        stamplist.append(tx["stamp"])
        except:
            data = []
            for block in chain["chain"]:
                for tx in block["transactions"]:
                    tx["hash"] = block["previous_hash"]
                    data.append(tx)

        # TODO remove dupes
        # save vals
        txwrite.seek(0)
        json.dump(data, txwrite)    
def show_posts():
    """
    Function to fetch posts from a json file and display them
    """
    fileread = open('logs/tx.json', 'r+')
    content = json.load(fileread)

    global posts
    posts = sorted(content, key=lambda k: k['datetime'],
                   reverse=True)

 

@app.route('/')
def index():
    fetch_posts()
    show_posts()
    actualIP = request.remote_addr
    for post in range (len(posts)):
        if (posts[post]['type'] == 'inscription' or posts[post]['type'] == 'update'):
            if (posts[post]['IP'] == actualIP): 
                return render_template('index.html',
                           title='YourNet: Decentralized '
                                 'content sharing',
                           posts = posts,
                           user_name = posts[post]['name'],
                           node_address = CONNECTED_NODE_ADDRESS,
                           readable_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")) 
    return redirect('/inscription')


@app.route('/inscription')
def inscription():
    return render_template('inscription.html',
                            title='YourNet: Decentralized '
                                 'content sharing',
                           node_address='{}node'.format(request.url_root) if RUNTIME_ENV == 'DOCKER_ENVIRONMENT' else CONNECTED_NODE_ADDRESS,
                           readable_time=datetime.now().strftime("%Y/%m/%d %H:%M:%S"))


@app.route('/submit-inscription', methods=['POST'])
def submit_textarea_i():

    name = request.form['name']

    post_object = {
        'type': "inscription",
        'name': name,
        'IP' : request.remote_addr,
        'content' : {
            'text': name + ' se ha inscrito.'
        },
        'datetime': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    }

    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/')


@app.route('/submit-transaction/user/<user_name>', methods=['POST'])
def submit_textarea_t(user_name):
    """
    Endpoint to create a new transaction via our application.
    """
    post_content = request.form["content"]
    
    post_object = {
        'type': 'transaction',
        'name' : user_name,
        'IP' : request.remote_addr,
        'content': {
            'text': post_content
        },
        'datetime': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    }

    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/')

#UPDATE IP
@app.route('/update_IP')
def update_IP():
    return render_template('update_ip.html',
                           title='YourNet: Decentralized '
                                 'content sharing',
                           node_address = CONNECTED_NODE_ADDRESS,
                           readable_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
            
@app.route('/submit_IP_update', methods=['POST'])
def submit_IP_update():
    name = request.form['name']

    
    """
    El front-end de la vista update_ip.html se puede cambiar por una lista de
    todos los usuarios que hay para que solo se deba seleccionar el usuario.
    De esta manera no existirá problema cuando el usuario digite un usuario
    que no se haya inscrito.

    Cuando esto se haya hecho se puede eliminar el for a continuación
    """

    for post in posts: 
        if (name == post['name']):
            previous_ip = post['IP']
    
    new_ip = request.remote_addr
    post_object = {
        'type': 'update',
        'name': name,
        'IP': new_ip,
        'content': {
            'text': name + ' ha cambiado de ip ' + previous_ip + ' a '+ new_ip,
            'previous_ip': previous_ip,
        },
        'datetime': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    }

    """
    Se debe de agregar el nodo con ip 'IP' y eliminar el nodo previous_ip.
    Se guardan cambios donde se almacene la información
    """
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    requests.post(new_tx_address,
                  json = post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/update_IP')
#-------------------------------------------
#UPDATE NAME
@app.route('/update_name')
def update_name():
    return render_template('update_name.html',
                           title='YourNet: Decentralized '
                                 'content sharing',
                           node_address = CONNECTED_NODE_ADDRESS,
                           readable_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
            
@app.route('/submit_name_update', methods=['POST'])
def submit_name_update():
    name = request.form['name']

    index = len(posts) - 1
    while(index != 0):
        if (posts[index]['IP'] == request.remote_addr):
            previous_name = posts[index]['name']
        index -=1

    new_ip = request.remote_addr
    post_object = {
        'type': 'update',
        'name': name,
        'IP': request.remote_addr,
        'content': {
            'text': name + ' ha cambiado su nombre de ' + previous_name + ' a '+ name,
            'previous_name': previous_name,
        },
        'datetime': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    }

    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    requests.post(new_tx_address,
                  json = post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/update_name')
#-------------------------------------------
#LEAVE
@app.route('/leave')
def leave():
    return render_template('leave.html',
                           title='YourNet: Decentralized '
                                 'content sharing',
                           node_address = CONNECTED_NODE_ADDRESS,
                           readable_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S"))

@app.route('/submit_leave', methods=['POST'])
def submit_leave():
 
    index = len(posts) - 1
    while(index >= 0):
        if (posts[index]['IP'] == request.remote_addr):
            name = posts[index]['name']
        index -=1

    new_ip = request.remote_addr
    post_object = {
        'type': 'leave',
        'name': name,
        'IP': request.remote_addr,
        'content': {
            'text': name + ' ha salido de la cadena',
            'previous_ip': request.remote_addr,
        },
        'datetime': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    }

    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    requests.post(new_tx_address,
                  json = post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/')