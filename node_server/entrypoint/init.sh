#!bin/sh

#Run flask app
./wait_for_mysql.sh && FLASK_APP=node_server.py flask run --port=8000 --host=0.0.0.0