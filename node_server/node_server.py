from flask import Flask, request
import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

    db.init_app(app)

    with app.app_context():
        import node_server.routes
        db.create_all()
        return app

