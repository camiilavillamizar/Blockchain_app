from datetime import datetime
import json

import requests
from flask import render_template, redirect, request

from app import app

# The node with which our application interacts, there can be multiple
# such nodes as well.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

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
    
    """
    #Cuando ya se tenga el frontend se puede descomentar esto y agregar en actualip la ip actual
    for post in range (len(posts)):
        if (post.IP == actualIP): #la proporciona el frontend
            return render_template('index.html',
                           title='YourNet: Decentralized '
                                 'content sharing',
                           posts = posts,
                           node_address = CONNECTED_NODE_ADDRESS,
                           readable_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")) 
    return redirect('/inscription')
    """
    return render_template('index.html',
                           title='YourNet: Decentralized '
                                 'content sharing',
                           posts=posts,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")) 

@app.route('/inscription')
def inscription():
    return render_template('inscription.html',
                            node_address = CONNECTED_NODE_ADDRESS,
                            readable_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S"))

@app.route('/submit-inscription', methods = ['POST'])
def submit_textarea_i():
    
    name = request.form['name']

    post_object = {
        'type': 'inscription', 
        'content': " ",
        'name': name, 
        'IP': 'Una IP'  #La proporciona el frontend
    }

    new_tx_address = "{}/new_inscription".format(CONNECTED_NODE_ADDRESS)
    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/inscription')

@app.route('/submit-transaction', methods=['POST'])
def submit_textarea_t():
    """
    Endpoint to create a new transaction via our application.
    """
    post_content = request.form["content"]

    post_object = {
        'type': 'transaction',
        'content': post_content,
        'name': 'Nombre',
        'IP' : 'IP',
    }

    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/')

