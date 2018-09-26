import os
from flask import Flask
import requests


# Generation of the flask webapp and adding config option to store data in
app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(os.path.abspath("db"), 'login.db')
app.config['MAIL_DEFAULT_SENDER'] = "aleddocteur@gmail.com"
app.config['MAIL_PASSWORD'] = "aledisis"
# Secret key for session
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or os.urandom(24)
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT') or os.urandom(24)

myFavoritePatient = ["5ba8b75b2eef950010bbb5b1"]
names = requests.get("https://fhir.eole-consulting.io/api/practitioner/5ba8b7752eef950010bbb5b4").json()["name"][0]
app.config["medecin"] = names["family"]+" "+names["given"][0]

