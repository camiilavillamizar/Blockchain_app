from zxcvbn import zxcvbn
from  zxcvbn.matching  import  add_frequency_lists 
import hashlib
import random
import string

from node_server.models import User
from node_server import db

def saving_password(tx_data):
    password = tx_data.get('password')

    name = tx_data['content']['name']
    results = zxcvbn(password, user_inputs= name)

    if results['score'] < 3:
        message = 'Insecure password. '

        if (results['feedback']['warning'] != ''):
            message += results['feedback']['warning']

        suggestions = results['feedback']['suggestions']
        if ( suggestions != '' and len(suggestions) >= 1):
            for i in suggestions:
                message += ' ' + i

        return message
    else:
        salt = ''
        for i in range (3):
            salt += random.choice(string.ascii_lowercase)

        password += salt
        hash_password = hashlib.sha256(str(password).encode('utf-8')).hexdigest()

        user = User(user_name=tx_data['user_name'], name=name, password=hash_password, salt=salt, ip=tx_data['IP'], email=tx_data['content']['email'])
        db.session.add(user)
        db.session.commit()

        return True