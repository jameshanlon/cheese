import datetime
import os
import sys
import re
from flask import Flask, render_template, render_template_string, request
from flask_flatpages import FlatPages
from flask_thumbnails import Thumbnail

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

app = Flask(__name__)
app.config.from_pyfile('settings.cfg')
pages = FlatPages(app)
thumb = Thumbnail(app)

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


def get_news():
    news_items = [x for x in pages if 'news' in x.meta]
    news_items = sorted(news_items, reverse=True,
                        key=lambda p: p.meta['date'])
    # Render any templating in each news item.
    for item in news_items:
        item.html = render_template_string(item.html)
        item.date_str = item.meta['date'].strftime('%B %Y')
    return news_items

@app.route('/')
def index():
    news_items = get_news()
    if len(news_items) >= 3:
        news_items = news_items[:3]
    return render_template('index.html', news_items=news_items)


@app.route('/<path:path>/')
def page(path):
    page = pages.get_or_404(path)
    template = page.meta.get('template', 'page.html')
    return render_template(template, page=page)


@app.route('/news')
def news():
    return render_template('news.html', news_items=get_news())


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
