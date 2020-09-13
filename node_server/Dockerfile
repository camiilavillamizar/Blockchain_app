FROM python:3.6.1-alpine
WORKDIR /node_server
ADD . /node_server
RUN pip install -r requirements.txt

RUN chmod a+x ./entrypoint/init.sh
ENTRYPOINT ["sh","./entrypoint/init.sh"]

