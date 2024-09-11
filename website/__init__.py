from flask import Flask
from os import path
from .database import db
from .models import Medicament
from .views import main


DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app = Flask(__name__, template_folder='templates')
    app.register_blueprint(main)
    app.config['SECRET_KEY'] = "helloworld"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

    db.init_app(app)

    create_database(app)

    return app


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
        print('Created Database!')