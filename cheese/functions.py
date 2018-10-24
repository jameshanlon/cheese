import datetime
import glob
import os
from cheese.views import s3
from flask import Blueprint, current_app, request
from werkzeug import url_encode

bp = Blueprint('functions', __name__)

@bp.app_template_global()
def modify_query(**new_values):
    args = request.args.copy()
    for key, value in new_values.items():
        args[key] = value
    return '{}?{}'.format(request.path, url_encode(args))

@bp.app_template_global()
def add_to_query(**new_values):
    args = request.args.copy()
    for key, value in new_values.items():
        args.add(key, value)
    return '{}?{}'.format(request.path, url_encode(args))

@bp.app_template_global()
def remove_from_query(**new_values):
    args = request.args.copy()
    for key, value in new_values.items():
        items = args.getlist(key)
        items.remove(value)
        args.setlist(key, items)
    return '{}?{}'.format(request.path, url_encode(args))

@bp.app_template_global()
def get_one_month_date(survey_date):
    return survey_date + datetime.timedelta(current_app.config['ONE_MONTH_FOLLOW_UP_DAYS'])

@bp.app_template_global()
def get_one_year_date(survey_date):
    return survey_date + datetime.timedelta(current_app.config['ONE_YEAR_FOLLOW_UP_DAYS'])

@bp.app_template_global()
def get_date_now():
    return datetime.datetime.now()

@bp.app_template_global()
def image_list(directory):
    files = s3.list_directory('images/'+directory)
    files = [x for x in files if \
              x.endswith(tuple(current_app.config['IMAGE_FORMATS']))]
    return files
