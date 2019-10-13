from flask import Blueprint, current_app, url_for
from cheese.thumbnail import get_thumbnail

bp = Blueprint('filters', __name__)

@bp.app_template_filter('format_db_name')
def format_db_name(name):
    name = name.replace('_', ' ')
    return name[0].upper() + name[1:]

@bp.app_template_filter('url_for_asset')
def url_for_asset(filename):
    return current_app.config['S3_URL_PREFIX']+'/'+filename

@bp.app_template_filter('thumbnail')
def thumbnail(filename, size):
    return get_thumbnail(filename, size)

@bp.app_template_filter('remove_tag_block')
def remove_tag_block(text, tag):
    return text[:text.find("<"+tag)] + text[text.find("</"+tag+">") + len(tag)+3:]
