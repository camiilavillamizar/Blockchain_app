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

def fetch_posts():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)

        global posts
        posts = sorted(content, key=lambda k: k['datetime'],
                       reverse=True)



@app.route('/')
def index():
    fetch_posts()
    actualIP = request.remote_addr
    for post in range (len(posts)):
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
                           node_address='{}node'.format(request.url_root) if RUNTIME_ENV == 'DOCKER_ENVIRONMENT' else CONNECTED_NODE_ADDRESS,
                           readable_time=datetime.now().strftime("%Y/%m/%d %H:%M:%S"))


@app.route('/submit-inscription', methods=['POST'])
def submit_textarea_i():

    name = request.form['name']

    post_object = {
        'type': "inscription",
        'name': name,
        'IP' : request.remote_addr,
        'content' : name + ' se ha inscrito.',
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
        'content': post_content,
        'datetime': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    }

    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/')

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

    
    #Si el nombre existe se cambia, si no, no
    post_object = {
        'type': 'update',
        'name': name,
        'IP': request.remote_addr,
        'content': name + ' ha actualizado su IP',
        'datetime': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    }

    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    requests.post(new_tx_address,
                  json = post_object,
                  headers={'Content-type': 'application/json'})