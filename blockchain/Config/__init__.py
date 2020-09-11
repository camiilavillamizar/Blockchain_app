import os
from dotenv import load_dotenv

## Loading env variables
# load dotenv in the base root
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

RUNTIME_ENV = os.environ.get('RUNTIME_ENV')

def connected_node_address( request):
    if request is not None:
        return '{}node'.format(request.url_root)
    else:
        return os.environ.get('CONNECTED_NODE_ADDRESS')