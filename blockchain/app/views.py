from datetime import datetime
import json

import requests
from flask import render_template, redirect, request

from app import app
import Config

TITLE = 'YourNet: Decentralized ' 'content sharing'

posts = []


def fetch_posts():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}/chain".format(
        Config.connected_node_address(request))
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


@app.route('/index')
@app.route('/')
def index():
    fetch_posts()
    return redirect('/login')

@app.route('/login')
def login():
    return render_template('login.html',
                           title=TITLE,
                           node_address=Config.connected_node_address(request),
                           readable_time=datetime.now().strftime("%Y/%m/%d %H:%M:%S"))


@app.route('/check_login', methods=['POST'])
def check_login():

    fetch_posts()
    user_name = request.form['user_name']
    actualIP = request.remote_addr
    leave = False
    update_name = False

    for post in posts:
        if (post['type'] == 'leave' and post['IP'] == actualIP):
            leave = True

    for post in posts:
        if (post['type'] == 'update' and post['IP'] == actualIP and post['content']['previous_name'] is not None):
            update_name = True
            name = post['content']['name']

    for post in posts:
        if user_name == post['user_name']:
            if (post['type'] == 'inscription' or (post['type'] == 'update' and 'previous_ip' in post['content'].keys())):
                if (post['IP'] == actualIP and leave == False):
                    if update_name != True: 
                        name = post['content']['name']
                    return render_template('index.html',
                                        title=TITLE,
                                        posts=posts,
                                        user_name=post['user_name'],
                                        name=name,
                                        node_address=Config.connected_node_address(
                                            request),
                                        readable_time=datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                    break
                else:
                    if leave == False:
                        #El usuario si existe pero la Ip no coincide
                        return render_template('update_ip.html',
                            title=TITLE,
                           user_name=user_name,
                           node_address=Config.connected_node_address(request),
                           readable_time=datetime.now().strftime("%Y/%m/%d %H:%M:%S"))


    return redirect('/login')

@app.route('/inscription')
def inscription():
    fetch_posts()
    return render_template('inscription.html',
                           title=TITLE,
                           node_address=Config.connected_node_address(request),
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
            return "Este usuario ya se encuentra registrado", 404

    post_object = {
        'type': "inscription",
        'user_name': user_name,
        'IP': request.remote_addr,
        'content': {
            'text': '{0} se ha inscrito.'.format(user_name),
            'name': name,
            'email': email
        },
        'datetime': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    }

    new_tx_address = "{}/new_transaction".format(
        Config.connected_node_address(request))
    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})
    
    new_tx_to_mine = "{}/mine".format(
        Config.connected_node_address(request))

    requests.get(new_tx_to_mine)

    return redirect('/')


@app.route('/submit-transaction/user/<user_name>', methods=['POST'])
def submit_textarea_t(user_name):
    
    """
    Endpoint to create a new transaction via our application.
    """
    post_content = request.form["content"]
    update_name = False
    for post in posts:
       if (post['type'] == 'update' and post['IP'] == actualIP and post['content']['previous_name'] is not None):
            update_name = True
            name = post['content']['name']
    
    for post in posts: 
        if post['user_name'] == user_name and post['type'] == 'inscription':
            if update_name == False:
                name = post['content']['name']

    post_object = {
        'type': 'transaction',
        'user_name': user_name,
        'IP': request.remote_addr,
        'content': {
            'text': post_content,
            'name': name
        },
        'datetime': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    }

    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(
        Config.connected_node_address(request))

    requests.post(new_tx_address, json=post_object, headers={'Content-type': 'application/json'})

    new_tx_to_mine = "{}/mine".format(Config.connected_node_address(request))

    requests.get(new_tx_to_mine)

    fetch_posts()
    return render_template('index.html', title=TITLE, posts=posts,
                            user_name= user_name, name=name,
                             node_address=Config.connected_node_address( request),
                            readable_time=datetime.now().strftime("%Y/%m/%d %H:%M:%S"))

# UPDATE IP

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
                'text': user_name + ' ha cambiado de ip ' + previous_ip + ' a ' + new_ip,
                'previous_ip': previous_ip,
            },
            'datetime': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        }

        """
        Se debe de agregar el nodo con ip 'IP' y eliminar el nodo previous_ip.
        """
        new_tx_address = "{}/new_transaction".format(
            Config.connected_node_address(request))
        requests.post(new_tx_address,
                      json=post_object,
                      headers={'Content-type': 'application/json'})
        new_tx_to_mine = "{}/mine".format(
        Config.connected_node_address(request))

        requests.get(new_tx_to_mine)

        return redirect('/login')
    except:
        return "You are not registered", 404
# -------------------------------------------
# UPDATE NAME


@app.route('/update_name')
def update_name():
    return render_template('update_name.html',
                           title=TITLE,
                           node_address=Config.connected_node_address(request),
                           readable_time=datetime.now().strftime("%Y/%m/%d %H:%M:%S"))


@app.route('/submit_name_update', methods=['POST'])
def submit_name_update():
    name = request.form['name']

    for post in reversed(posts):
        if post['IP'] == request.remote_addr and post['content']['name'] is not None:
            previous_name = post['content']['name']
            user_name = post['user_name']

    post_object = {
        'type': 'update',
        'user_name': user_name,
        'IP': request.remote_addr,
        'content': {
            'text': user_name + ' ha cambiado su nombre de ' + previous_name + ' a ' + name,
            'previous_name': previous_name,
            'name': name
        },
        'datetime': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    }
    #ACTUALIZAR EN LA DB QUE SE CAMBIÓ EL NOMBRE 
    new_tx_address = "{}/new_transaction".format(
        Config.connected_node_address(request))
    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    new_tx_to_mine = "{}/mine".format(
        Config.connected_node_address(request))

    requests.get(new_tx_to_mine)

    return redirect('/')

# -------------------------------------------
# LEAVE


@app.route('/leave')
def leave():
    return render_template('leave.html',
                           title='YourNet: Decentralized '
                                 'content sharing',
                           node_address=Config.connected_node_address(request),
                           readable_time=datetime.now().strftime("%Y/%m/%d %H:%M:%S"))


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

    new_tx_address = "{}/new_transaction".format(
        Config.connected_node_address(request))
    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})
    new_tx_to_mine = "{}/mine".format(
        Config.connected_node_address(request))

    requests.get(new_tx_to_mine)

    return redirect('/login')
