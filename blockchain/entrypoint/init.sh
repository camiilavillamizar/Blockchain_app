#!bin/sh

#Run flask app
./wait_for_mysql.sh && FLASK_APP=front_end.py flask run --port=5000 --host=0.0.0.0