FROM python:3.6.1-alpine
WORKDIR /blockchain
ADD . /blockchain
RUN pip install -r requirements.txt
CMD ["python","run_app.py"]