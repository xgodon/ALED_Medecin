from itsdangerous import URLSafeTimedSerializer
from utils.app_init import *
from flask import url_for, render_template, request, flash
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from utils.database import isHere


def send_email(email, subject, html):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = app.config['MAIL_DEFAULT_SENDER']
    msg['To'] = email
    msg.attach(MIMEText(html, 'html'))

    # Send the message via outlook SMTP server.
    mailserver = smtplib.SMTP('smtp.gmail.com', 587)
    mailserver.ehlo()
    mailserver.starttls()
    mailserver.ehlo()
    mailserver.login(msg['From'], app.config['MAIL_PASSWORD'])
    mailserver.sendmail(msg['From'], msg['To'], msg.as_string())
    mailserver.quit()


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email


def send_activate(mail):
    send_confirm(mail, "subTemplates/activate.html", "confirm_email", "Confirm your email")


def send_confirm(mail,template,uri,subject):
    # Now we'll send the email confirmation link
    subject = subject
    token = generate_confirmation_token(mail)
    url = url_for(
        uri,
        token=token,
        _external=True)

    html = render_template(
        template,
        confirm_url=url,
        base_url = request.url_root)

    send_email(mail, subject, html)


@app.route("/sendConfirm", methods=['POST'])
def confirm():
    mail = request.form.get('mail')
    send_activate(mail)
    return ""


@app.route("/resetPass", methods=['POST'])
def reset():
    mail = request.form.get('mail')
    if isHere(mail):
        send_confirm(mail, "subTemplates/newPass.html", "reset_pass", "Reset your password")
    return ""
