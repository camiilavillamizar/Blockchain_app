FROM python:3.6.1-alpine
WORKDIR /node_server
ADD . /node_server
RUN pip install -r requirements.txt
ENV FLASK_APP=node_server.py
CMD flask run --port=8000 --host=0.0.0.0

