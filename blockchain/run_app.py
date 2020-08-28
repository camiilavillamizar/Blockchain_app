import os
from app import app

app.run(debug=True, port=os.environ.get('flask_port',5000), host='0.0.0.0')
