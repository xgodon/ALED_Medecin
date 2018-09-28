from flask import render_template, redirect, request, abort
from flask_login import login_required, logout_user
from utils.token import confirm_token, send_activate
from utils.database import *
from werkzeug.utils import secure_filename
import requests
import json

base_URL = "https://fhir.eole-consulting.io/api/"
userID = "5ba8b7752eef950010bbb5b4"


def getMyAppointements():
    res = requests.get(base_URL+"appointment?participant.actor.reference=Practitioner/"+userID).json()
    ldmc = []
    for liste in res:
        id = liste["id"]
        try:
            reason = liste["appointmentType"]["coding"][0]["display"]
        except KeyError:
            reason = "Auncune raison"
        try:
            start = tranformDate(liste["requestedPeriod"][0]["start"])
            end = tranformDate(liste["requestedPeriod"][0]["end"])
        except KeyError:
            start = "Non spécifié"
            end = start
        name = "JM"
        try:
            status = liste["status"]
        except KeyError:
            status = "Non spécifié"
        for element in liste["participant"]:
            if "Patient" in element["actor"]["reference"]:
                name = element["actor"]["display"]

        ldmc.append({"id":id, "type":status, "name": name, "reason": reason, "start":start, "end":end})
    return ldmc

def tranformDate(date):
    date = date.replace("T"," ")
    date = date.replace(":00.000Z", "")
    return date

@app.route('/')
def main():
    patient = getAllPatientData()
    return render_template("index.html", patients=patient)


@app.route('/calendar')
def calendar():
    return render_template("planning.html", booked = getMyAppointements())


@app.route('/refuseAppointment', methods=['GET', 'POST'])
def refuse():
    if request.method == "POST":
        id = request.form.get("id")
        res = get("appointment", id).json()
        res["status"] = "cancelled"
        put("appointment", json.dumps(res), id)
    return appointment()


@app.route('/scheduleAppointment', methods=['GET', 'POST'])
def schedule():
    if request.method == "POST":
        id = request.form.get("id")
        start = request.form.get("start")
        end = request.form.get("end")
        print(start, end)
        res = get("appointment", id).json()
        res["status"] = "pending"
        put("appointment", json.dumps(res), id)
    return appointment()


@app.route('/newObservation', methods=['GET', 'POST'])
def postObservation():
    now = datetime.datetime.now()
    id = request.form.get('patientID')
    nb_kilo = request.form.get('weight')
    resu = {
        "resourceType": "Observation",
        "status": "final",
        "performer": [
          {
            "reference": "Practitioner/"+userID
          }],
        "subject": {
            "reference": "Patient/"+id
        },
        "effectiveDateTime": "2018-09-28T00:10:30.000Z",
        "category": [
            {
            "coding": [
                {
                  "system": "http://hl7.org/fhir/observation-category",
                  "code": "vital-signs",
                  "display": "Vital Signs"
                }
              ]
            }
        ],
        "code": {
            "coding": [
              {
                "system": "http://loinc.org",
                "code": "29463-7",
                "display": "Body Weight"
              },
              {
                "system": "http://loinc.org",
                "code": "3141-9",
                "display": "Body weight Measured"
              },
              {
                "system": "http://snomed.info/sct",
                "code": "27113001",
                "display": "Body weight"
              },
              {
                "system": "http://acme.org/devices/clinical-codes",
                "code": "body-weight",
                "display": "Body Weight"
              }
            ]
          },
        "valueQuantity": {
        "value": int(nb_kilo),
        "unit": "kg"
        }
    }
    print(post("observation", json.dumps(resu), id).content)
    return main()


@app.route('/acceptAppointment', methods=['GET', 'POST'])
def accept():
    if request.method == "POST":
        id = request.form.get("id")
        res = get("appointment", id).json()
        res["status"] = "booked"
        put("appointment", json.dumps(res), id)
    return appointment()


@app.route('/appointment')
def appointment():
    appointements = getMyAppointements()
    res = []
    for element in appointements:
        try:
            if element["type"] == "proposed" or element["type"] == "pending":
                res.append(element)
        except KeyError:
            pass
    return render_template("appointment.html", patients=res)


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
    try:
        name = res["name"][0]
        family = name["family"]
        name = " ".join(name["given"])
    except KeyError:
        name = "Le keum a pas de nom"
        family = "Gros boulet"
    try:
        gender = res["gender"]
        if gender == "male":
            gender = "Monsieur"
        elif gender == "female":
            gender = "Madame"
        else:
            gender = "Non Binaire"
    except KeyError:
        gender = "Fais pas nimp"
    telecom = res["telecom"][1]["value"]
    address = res["address"][0]["text"]
    return gender, family, name, telecom, address


def getAllPatientData():
    myPatients = []
    patientsID = getAllPatientId()
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


def put(job, datas, id):
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    res = requests.put(base_URL+job+"/"+id, data = datas, headers=headers)
    return res


def post(job, datas, id):
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    res = requests.post(base_URL+job+"/"+id, data = datas, headers=headers)
    return res


def get(job, id):
    res = requests.get(base_URL+job+"/"+id)
    return res


if __name__ == '__main__':
    app.config["medecin"] = get("practitioner", "5ba8b7752eef950010bbb5b4").json()
    app.run()
