from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()
class User(db.Model):
    user_name: str
    name: str
    password : str
    ip: str
    email: str

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(180), index=False, unique=False, nullable=True)
    name = db.Column(db.String(180), index=False, unique=False, nullable=True)
    password = db.Column(db.PickleType, index=False, unique=False, nullable=True)
    ip = db.Column(db.String(180), index=False, unique=False, nullable=False)
    email = db.Column(db.String(180), index=False, unique=False, nullable=True)

    def __init__(self, email, name, password, ip, user_name):
        self.email = email
        self.password = password
        self.ip = ip
        self.user_name = user_name

    def encrypt_password(self, password):
        return password

    def serialize(self):
        return {
            'user_name': self.user_name,
            'name': self.name,
            'ip': self.ip,
            'email': self.email
        }

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

    db.init_app(app)
    
    with app.app_context():
        import blockchain.views
        db.create_all()
        return app