FROM python:3

ADD . /ALED_Medecin

WORKDIR  /ALED_Medecin 

RUN apt-get update
RUN pip install -r /ALED_Medecin/requirement.txt
RUN export FLASK_APP=app.py
RUN chmod +x /ALED_Medecin/entrypoint.sh

ENTRYPOINT /ALED_Medecin/entrypoint.sh

EXPOSE 5000