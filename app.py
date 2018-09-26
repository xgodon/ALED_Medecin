from flask import render_template, redirect, request, abort
from flask_login import login_required, logout_user
from utils.token import confirm_token, send_activate
from utils.database import *
from werkzeug.utils import secure_filename
import requests

base_URL = "https://fhir.eole-consulting.io/api/"

@app.route('/')
def main():
    patient = getAllPatientData()
    return render_template("index.html", patients=patient)


@app.route('/calendar')
def calendar():
    return render_template("planning.html")\



@app.route('/appointment')
def appointment():
    patient = getAllPatientData()
    return render_template("appointment.html", patients=patient)


# The login/logout part only front end for the moment
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Only usable in a POST context
    if request.method == 'POST':
        user = request.form.get("email")
        pwd = request.form.get("password")
        remember = request.form.get("remember") is not None
        log(user, pwd, remember)
        return redirect("/")
    return render_template('login.html')


@app.route("/logout", methods=['GET'])
def logout():
    logout_user()
    return redirect("/login")


@app.route('/register', methods=['GET', 'POST'])
def register():
    user = ""
    mail = ""
    # Only usable in a POST context
    if request.method == 'POST':
        mail = request.form.get("email")
        user = request.form.get("username")
        pwd = request.form.get("password")
        pwds = request.form.get("password2")
        added = add_user(mail=mail, username=user, password=pwd, pwd_string=pwds)
        if added:
            send_activate(mail=mail)
            return redirect("/login")
    return render_template('register.html', mail=mail, username=user)


@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        abort(404)

    user = User.query.filter_by(mail=email).first_or_404()
    user.confirmed = True
    db.session.commit()
    flash("Your Account has been successfully activated", "Account Activated")
    return redirect("/login")


@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_pass(token):
    try:
        email = confirm_token(token)
    except:
        abort(404)

    if request.method == "POST":
        passw = request.form.get("pass")
        pwd = request.form.get("pwd")
        if isPassword(pwd):
            if pwd == passw:
                user = User.query.filter_by(mail=email).first_or_404()
                user.password = hash_func(pwd)
                db.session.commit()
                flash("Password Change successful", "Success")
                return redirect("/login")
            flash("Passwords are not matching", "Error")
        flash("Password must contain at least one uppercase, one lowercase, one digit, one special and have a minimum length of 8", "Error")

    return render_template("subTemplates/passReset.html", mail=email)


def getPatient(id):
    res = get("patient", id).json()
    return res


def getPatientData(id):
    res = getPatient(id)
    name = res["name"][0]
    family = name["family"]
    name = " ".join(name["given"])
    gender = res["gender"]
    telecom = res["telecom"][1]["value"]
    address = res["address"][0]["text"]
    if gender == "male":
        gender = "Monsieur"
    elif gender == "female":
        gender = "Madame"
    else:
        gender = "Non Binaire"
    return gender, family, name, telecom, address


def getAllPatientData():
    myPatients = []
    patientsID = getAllPatientId()
    print(patientsID)
    for id in patientsID:
        myPatients.append(getPatientData(id))
    return myPatients


def getAllPatientId():
    res = requests.get(base_URL + 'patient').json()
    patientId = []
    for element in res:
        patientId.append(element["id"])
    return patientId


def delete(job, id):
    res = requests.delete(base_URL+job+"/"+id)
    return res


def put(job, data, id):
    res = requests.put(base_URL+job+"/"+id, data)
    return res


def get(job, id):
    res = requests.get(base_URL+job+"/"+id)
    return res


if __name__ == '__main__':
    app.config["medecin"] = get("practitioner", "5ba8b7752eef950010bbb5b4").json()
    app.run()
