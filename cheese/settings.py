import os

APP_NAME               = 'The CHEESE Project'
SECRET_KEY             = os.environ['CHEESE_SECRET_KEY']
CSRF_ENABLED           = True
FLATPAGES_EXTENSION    = '.md'
ADMINS                 = os.environ['CHEESE_ADMINS']
# Media
MEDIA_FOLDER           = 'cheese/'
MEDIA_URL              = '/'
MEDIA_THUMBNAIL_FOLDER = 'cheese/static/images/thumbs'
UPLOADED_IMAGES_DEST   = 'cheese/static/uploads'
MEDIA_THUMBNAIL_URL    = '/static/images/thumbs/'
MAX_IMAGE_SIZE         = 4*1024*1024 # 4 MB
# Flask-Mail
MAIL_SERVER            = os.environ['CHEESE_SMTP_SERVER']
MAIL_USERNAME          = os.environ['CHEESE_SMTP_USERNAME']
MAIL_PASSWORD          = os.environ['CHEESE_SMTP_PASSWORD']
MAIL_DEFAULT_SENDER    = os.environ['CHEESE_EMAIL_SENDER']
MAIL_PORT              = int(os.environ['CHEESE_SMTP_PORT'])
MAIL_USE_SSL           = int(os.environ['CHEESE_SMTP_USE_SSL'])
MAIL_USE_TLS           = int(os.environ['CHEESE_SMTP_USE_TLS'])
# MySQL
MYSQL_HOST             = os.environ['CHEESE_MYSQL_HOST']
MYSQL_DATABASE         = os.environ['CHEESE_MYSQL_DATABASE']
MYSQL_USER             = os.environ['CHEESE_MYSQL_USER']
MYSQL_PASSWORD         = os.environ['CHEESE_MYSQL_PASSWORD']
SQLALCHEMY_TRACK_MODIFICATIONS = False
if 'CHEESE_TESTING' in os.environ:
    # Settings for testing.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    WTF_CSRF_ENABLED = False
    DEBUG = True
else:
    # Settings for deployment.
    SQLALCHEMY_DATABASE_URI = \
        'mysql://'+MYSQL_USER+':'+MYSQL_PASSWORD \
            +'@'+MYSQL_HOST+'/'+MYSQL_DATABASE
# Flask-User settings
USER_APP_NAME               = APP_NAME
USER_ENABLE_CHANGE_PASSWORD = True
USER_ENABLE_CONFIRM_EMAIL   = True
USER_ENABLE_FORGOT_PASSWORD = True
USER_ENABLE_EMAIL           = True
USER_ENABLE_REGISTRATION    = True
USER_ENABLE_RETYPE_PASSWORD = True
USER_ENABLE_USERNAME        = False
USER_ENABLE_CHANGE_USERNAME = False
USER_ENABLE_INVITATION      = True
USER_REQUIRE_INVITATION     = True
USER_AFTER_LOGIN_ENDPOINT   = 'index'
USER_AFTER_LOGOUT_ENDPOINT  = 'index'
