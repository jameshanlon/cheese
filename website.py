import os
import sys
from flask import Flask, render_template, request

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

app = Flask(__name__)

SMTP_SERVER = os.environ['SMTP_SERVER']
USERNAME    = os.environ['USERNAME']
PASSWORD    = os.environ['PASSWORD']
SENDER      = os.environ['SENDER']
RECEIVER    = os.environ['RECEIVER']


def send_email(subject, message):
    msg = MIMEMultipart()
    msg['From'] = SENDER
    msg['To'] = RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(message))
    mailserver = smtplib.SMTP(SMTP_SERVER, 587)
    mailserver.ehlo()
    mailserver.starttls()
    mailserver.ehlo()
    mailserver.login(USERNAME, PASSWORD)
    mailserver.sendmail(SENDER, RECEIVER, msg.as_string())
    mailserver.quit()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/apply-for-a-survey', methods=['GET', 'POST'])
def apply_for_a_survey():
    if request.method == 'POST':
        name              = request.form['name']
        address           = request.form['address']
        telephone         = request.form['telephone']
        email             = request.form['email']
        availability      = request.form['availability']
        house_type        = request.form['house-type']
        house_type_other  = request.form['house-type-other']
        number_receptions = request.form['number-receptions']
        number_bedrooms   = request.form['number-bedrooms']
        free_survey = 'yes' if 'free-survey' in request.form else 'no'
        subject = 'Request for a survey'
        message =  'Name: '+name+'\n'
        message += 'Address: '+address+'\n'
        message += 'Telephone: '+telephone+'\n'
        message += 'Email: '+email+'\n'
        message += 'Availability: '+availability+'\n'
        message += 'House type: '+house_type+'\n'
        message += 'If \'other\': '+house_type_other+'\n'
        message += 'Number of reception rooms: '+number_receptions+'\n'
        message += 'Number of bedrooms: '+number_bedrooms+'\n'
        message += 'Consideration for a free survey?: '+free_survey+'\n'
        send_email(subject, message)
        return render_template('application_successful.html')
    return render_template('apply_for_a_survey.html')

@app.route('/get-involved')
def get_involved():
    return render_template('get_involved.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
