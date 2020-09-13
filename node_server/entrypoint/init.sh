#!bin/sh

#initalice database
python3 ./database/init_database.py

#Run flask app
FLASK_APP=node_server.py flask run --port=8000 --host=0.0.0.0