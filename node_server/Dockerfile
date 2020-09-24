FROM python:3.6.1-alpine

RUN apk add --no-cache mariadb-client

WORKDIR /node_server

COPY  requirements.txt ./

RUN pip install -r requirements.txt

ADD . /node_server


RUN chmod a+x ./entrypoint/init.sh
RUN chmod a+x ./wait_for_mysql.sh
ENTRYPOINT ["sh","./entrypoint/init.sh"]

