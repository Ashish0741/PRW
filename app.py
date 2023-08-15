from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_migrate import Migrate
from flask_mail import Mail

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.debug = True

# Database configuration

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///productrental.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db,render_as_batch=True)


# Email configuration

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'product.rental09@gmail.com'
app.config['MAIL_PASSWORD'] = 'luhxxqxygbawygxb'

mail = Mail(app)

# module impoting

from routes import *

from models import *


# creating all tables
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run()