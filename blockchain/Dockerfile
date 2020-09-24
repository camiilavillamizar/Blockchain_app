FROM python:3.6.1-alpine
WORKDIR /blockchain
COPY  requirements.txt ./
RUN pip install -r requirements.txt

ADD . /blockchain

CMD ["python","run_app.py"]