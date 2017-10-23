import datetime
import glob
import os
from flask import request
from werkzeug import url_encode
from cheese.init_app import app

@app.template_global()
def modify_query(**new_values):
    args = request.args.copy()
    for key, value in new_values.items():
        args[key] = value
    return '{}?{}'.format(request.path, url_encode(args))

@app.template_global()
def add_to_query(**new_values):
    args = request.args.copy()
    for key, value in new_values.items():
        args.add(key, value)
    return '{}?{}'.format(request.path, url_encode(args))

@app.template_global()
def remove_from_query(**new_values):
    args = request.args.copy()
    for key, value in new_values.items():
        items = args.getlist(key)
        items.remove(value)
        args.setlist(key, items)
    return '{}?{}'.format(request.path, url_encode(args))

@app.template_global()
def get_one_month_date(survey_date):
    return survey_date + datetime.timedelta(app.config['ONE_MONTH_FOLLOW_UP_DAYS'])

@app.template_global()
def get_one_year_date(survey_date):
    return survey_date + datetime.timedelta(app.config['ONE_YEAR_FOLLOW_UP_DAYS'])

@app.template_global()
def get_date_now():
    return datetime.datetime.now()

@app.template_global()
def image_list(directory, ext='.jpg'):
    return ['static/images/'+directory+'/'+os.path.basename(x) \
              for x in glob.glob(app.config['IMAGES_DIR']+'/'+directory+'/*'+ext)]
