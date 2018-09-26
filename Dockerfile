FROM debian

ADD . /ALED_Medecin
RUN apt-get update
RUN apt-get install -y python3-pip

WORKDIR  /ALED_Medecin 
RUN venv/bin/activate
RUN pip install Flask
RUN export FLASK_APP=app.py
RUN flask run

EXPOSE 5000