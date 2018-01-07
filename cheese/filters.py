from flask import Blueprint

bp = Blueprint('filters', __name__)

@bp.app_template_filter('format_db_name')
def format_db_name(name):
    name = name.replace('_', ' ')
    return name[0].upper() + name[1:]
