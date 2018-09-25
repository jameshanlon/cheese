from flask import Blueprint, current_app, url_for
from cheese.thumbnail import get_thumbnail

bp = Blueprint('filters', __name__)

@bp.app_template_filter('format_db_name')
def format_db_name(name):
    name = name.replace('_', ' ')
    return name[0].upper() + name[1:]

@bp.app_template_filter('url_for_asset')
def url_for_asset(filename):
    return current_app.config['S3_PREFIX']+'/'+filename

@bp.app_template_filter('thumbnail')
def thumbnail(filename, size):
    return get_thumbnail(filename, size)
