from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user
from flask import redirect, flash, session
from sqlalchemy import exc, ForeignKey
from passlib.hash import argon2
import re
import datetime
from utils.app_init import app

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


def hash_func(pwd_string):
    return argon2.using(rounds=4).hash(pwd_string)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(12), unique=True, nullable=False)
    mail = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    register_date = db.Column(db.DATETIME, nullable=False, default=datetime.datetime.now())
    confirmed = db.Column(db.Boolean, nullable=False, default=False)


class BI(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    datasetID = db.Column(db.String(50), unique=True, nullable=False)
    reportID = db.Column(db.String(50), unique=True, nullable=False)
    ownerID = db.Column(db.String(50), ForeignKey("user.id"), nullable=False)


class Dataset(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    path = db.Column(db.String(50), unique=True, nullable=False)
    ownerID = db.Column(db.String(50), ForeignKey("user.id"), nullable=False)


def add_bi(name, datasetID, reportID, ownerID):
    try:
        bi = BI(name=name, datasetID=datasetID, reportID=reportID, ownerID=ownerID)
        db.session.add(bi)
        db.session.commit()
        return bi.id
    except exc.IntegrityError as e:
        db.session.rollback()


def add_dataset(name, path, ownerID):
    try:
        ds = Dataset(name=name, path=path, ownerID=ownerID)
        db.session.add(ds)
        db.session.commit()
        return ds.id
    except exc.IntegrityError as e:
        db.session.rollback()


def get_dataset_info(id):
    try:
        ds = Dataset.query.filter_by(id=id).first()
        return ds.name, ds.path, ds.ownerID

    except exc.NoReferencedTableError as e:
        return None, None, None


def remove_dataset(id):
    try:
        Dataset.query.filter_by(id=id).delete()
        db.session.commit()
        return True

    except exc.NoReferencedTableError as e:
        db.session.rollback()


def remove_bi(bi_id):
    try:
        BI.query.filter_by(reportID=bi_id).delete()
        db.session.commit()
        return True

    except exc.NoReferencedTableError as e:
        db.session.rollback()


def get_dataset(bi_id):
    try:
        bi = BI.query.filter_by(reportID=bi_id).first()
        return bi.datasetID

    except exc.NoReferencedTableError as e:
        db.session.rollback()


def get_reports(ownerID):
    try:
        return {bi.name: bi.reportID for bi in BI.query.filter_by(ownerID=ownerID).all()}
    except:
        return False


def add_user(username, mail, password, pwd_string):
    flash_string = ""
    if isMail(mail):
        if isPassword(password):
            if password == pwd_string:
                if 13 > len(username) > 2:
                    try:
                        user = User(username=username, mail=mail, password=hash_func(password))
                        db.session.add(user)
                        db.session.commit()
                        flash("A confirmation mail has been sent to "+mail, "Confirmation sent")
                        return True
                    except exc.IntegrityError as e:
                        if "user.username" in str(e):
                            flash_string = "This username is taken"
                        if "user.mail" in str(e):
                            flash_string = "This e-mail is taken"
                        db.session.rollback()
                else:
                    flash_string = "Username must be 3 to 12 characters long"
            else:
                flash_string = "Passwords not matching"
        else:
            flash_string = "Passwords must contain lowercase, uppercase letter and special characters and be at least 8 characters long"
    else:
        flash_string = "Mail is incorrect"
    flash(flash_string, "The details are incorrect")
    return False


def log(account, password, remember):
    if isMail(account):
        # TODO: store encrypted email addresses
        user = User.query.filter_by(mail=account).first()
        session["mail"] = account
    else:
        user = User.query.filter_by(username=account).first()
    if user and argon2.verify(password, user.password):
        session["mail"] = user.mail
        if user.confirmed:
            login_user(user, remember=remember)
            return current_user
        else:
            flash("Your user account is not activated", "Not Activated")
            return "Not confirmed"
    else:
        flash("Try again or use forgotten password button", "Bad Credentials")
        return "Bad Credentials"

"""
db.drop_all()
db.create_all()
user = User(username="username", mail="mail@mail.com", password=hash_func("password"),confirmed=True)
db.session.add(user)
user = User(username="user", mail="mail2@mail.com", password=hash_func("password"),confirmed=True)
db.session.add(user)
db.session.commit()"""


def isMail(string):
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", string))


def isPassword(string):
    return bool(re.match("^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[$@$!%*?&])[A-Za-z\d$@$!%*?&]{8,}", string))


def isHere(string):
    if isMail(string):
        return 0 < User.query.filter_by(mail=string).count()
    return False


@app.errorhandler(401)
def unauthorized(e):
    return redirect("/login")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))