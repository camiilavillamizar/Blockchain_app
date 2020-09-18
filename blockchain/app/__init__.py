from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = '-1982825246'

from app import views
