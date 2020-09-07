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
    leave = False
    
    for post in posts: 
        if (post['type'] == 'leave' and post['IP'] == actualIP):
            leave = True 

    for post in posts:
        if (post['type'] == 'inscription' or (post['type'] == 'update' and 'previous_ip' in post['content'].keys())):
            if (post['IP'] == actualIP and leave == False): 
                return render_template('index.html', title='YourNet: Decentralized ' 'content sharing', posts = posts,
                           user_name = post['user_name'], name = post['content']['name'],
                           node_address = CONNECTED_NODE_ADDRESS, readable_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")) 
                break
    return redirect('/inscription')


@app.route('/inscription')
def inscription():
    fetch_posts()
    leave = False
    actualIP = request.remote_addr

    for post in posts: 
        if (post['type'] == 'leave' and post['IP'] == actualIP):
            leave = True 

    for post in posts: 
        if post['type'] == 'inscription' or (post['type'] == 'update' and 'previous_ip' in post['content'].keys()):
            if( post['IP'] == request.remote_addr and leave == False):
                return redirect('/')
   
    return render_template('inscription.html', title='YourNet: Decentralized ' 'content sharing',
                           node_address='{}node'.format(request.url_root) if RUNTIME_ENV == 'DOCKER_ENVIRONMENT' else CONNECTED_NODE_ADDRESS,
                           readable_time=datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    
@app.route('/submit-inscription', methods=['POST'])
def submit_textarea_i():

    fetch_posts()
    user_name = request.form['user_name']
    name = request.form['name']
    email = request.form['email']
    not_allowed = False

    for post in posts:
        if (post['user_name'] == user_name): 
            us = post['user_name']
            not_allowed = True

    for post in reversed(posts):
        if (post['type'] == 'update' and 'previous_name' in post['content'].keys()):
            if (us == post['content']['previous_name']):
                not_allowed = False

    if not_allowed == True:
        return "Este usuario ya se encuentra registrado", 404

    post_object = {
        'type': "inscription",
        'user_name': user_name,
        'IP' : request.remote_addr,
        'content' : {
            'text': user_name + ' se ha inscrito.',
            'name': name,
            'email': email
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
        'user_name' : user_name,
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
    user_name = request.form['user_name']

    try: 
        for post in reversed(posts): 
            if (user_name == post['user_name']):
                previous_ip = post['IP']
        
        new_ip = request.remote_addr
        post_object = {
            'type': 'update',
            'user_name': user_name,
            'IP': new_ip,
            'content': {
                'text': user_name + ' ha cambiado de ip ' + previous_ip + ' a '+ new_ip,
                'previous_ip': previous_ip,
            },
            'datetime': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        }

        """
        Se debe de agregar el nodo con ip 'IP' y eliminar el nodo previous_ip.
        """
        new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
        requests.post(new_tx_address,
                    json = post_object,
                    headers={'Content-type': 'application/json'})

        return redirect('/update_IP')
    except:
        return "You are not registered", 404
#-------------------------------------------
#UPDATE NAME
@app.route('/update_user_name')
def update_user_name():
    return render_template('update_user_name.html',
                           title='YourNet: Decentralized '
                                 'content sharing',
                           node_address = CONNECTED_NODE_ADDRESS,
                           readable_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
            
@app.route('/submit_user_name_update', methods=['POST'])
def submit_user_name_update():
    user_name = request.form['user_name']

    for post in reversed(posts): 
        if post['IP'] == request.remote_addr:
            previous_user_name = post['user_name']
            if previous_user_name == user_name:
                return "No puede cambiar su usuario por el mismo", 404

    new_ip = request.remote_addr
    post_object = {
        'type': 'update',
        'user_name': user_name,
        'IP': request.remote_addr,
        'content': {
            'text': user_name + ' ha cambiado su usuario de ' + previous_user_name + ' a '+ user_name,
            'previous_user_name': previous_user_name,
        },
        'datetime': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    }

    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    requests.post(new_tx_address,
                  json = post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/update_user_name')
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

    for post in reversed(posts): 
        if post['IP'] == request.remote_addr:
            user_name = post['user_name']

    post_object = {
        'type': 'leave',
        'user_name': user_name,
        'IP': request.remote_addr,
        'content': {
            'text': user_name + ' ha salido de la cadena',
            'previous_ip': request.remote_addr,
        },
        'datetime': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    }

    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    requests.post(new_tx_address,
                  json = post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/leave')