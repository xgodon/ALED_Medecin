from flask import Flask
from flask import render_template
import requests

app = Flask(__name__)
base_URL = "https://fhir.eole-consulting.io/api/"

myFavoritePatient = ["5ba8b75b2eef950010bbb5b1"]
names = requests.get("https://fhir.eole-consulting.io/api/practitioner/5ba8b7752eef950010bbb5b4").json()["name"][0]
app.config["medecin"] = names["family"]+" "+names["given"][0]


@app.route('/')
def main():
    patient = getAllPatientData()
    print(patient)
    return render_template("index.html", patients=patient)


@app.route('/calendar')
def calendar():
    return render_template("planning.html")


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
