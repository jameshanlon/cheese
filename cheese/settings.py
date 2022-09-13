import datetime
import os

DEBUG = False
if 'FLASK_ENV' in os.environ and os.environ['FLASK_ENV'] == 'development':
  DEBUG = True
  TESTING = True # Supress mail being sent and don't source config from env.

APP_NAME                         = 'The CHEESE Project'
URL_BASE                         = 'https://cheeseproject.co.uk'
CSRF_ENABLED                     = True
FLATPAGES_EXTENSION              = '.md'
SYSTEM_ERROR_SUBJECT_LINE        = 'CHEESE webiste error'
LOG_FILENAME_INFO                = 'cheese.log'
LOG_FILENAME_ERROR               = 'cheese-error.log'
SECRET_KEY                       = os.environ['CHEESE_SECRET_KEY']
ADMINS                           = os.environ['CHEESE_ADMINS'].split(';')
WATCHERS                         = os.environ['CHEESE_WATCHERS'].split(';')
# S3
S3_BUCKET                        = 'jwh'
S3_PREFIX                        = 'cheese'
S3_URL_PREFIX                    = os.environ['CHEESE_S3_URL_PREFIX']
S3_REGION                        = os.environ['CHEESE_S3_REGION']
S3_ENDPOINT_URL                  = os.environ['CHEESE_S3_ENDPOINT_URL']
S3_ACCESS_KEY_ID                 = os.environ['CHEESE_S3_ACCESS_KEY_ID']
S3_SECRET_ACCESS_KEY             = os.environ['CHEESE_S3_SECRET_ACCESS_KEY']
# Media
THUMBNAIL_ROOT                   = 'cheese/static/thumbs'
THUMBNAIL_URL                    = '/static/thumbs'
MAX_CONTENT_LENGTH               = 4*1024*1024 # 4 MB
EXPORT_DIR                       = 'static/export'
EXPORT_PATH                      = 'cheese/'+EXPORT_DIR
IMAGES_DIR                       = 'cheese/static/images'
THUMB_SIZE                       = '200x200'
IMAGE_FORMATS                    = ['jpg', 'jpe', 'jpeg', 'png', 'gif', 'bmp']
# Uploads
UPLOADED_IMAGES_URL              = 'assets/uploads'
UPLOADED_IMAGES_PREFIX           = 'uploads'
# Flask-Mail
MAIL_SERVER                      = os.environ['CHEESE_SMTP_SERVER']
MAIL_USERNAME                    = os.environ['CHEESE_SMTP_USERNAME']
MAIL_PASSWORD                    = os.environ['CHEESE_SMTP_PASSWORD']
MAIL_DEFAULT_SENDER              = os.environ['CHEESE_EMAIL_SENDER']
MAIL_PORT                        = int(os.environ['CHEESE_SMTP_PORT'])
MAIL_USE_SSL                     = int(os.environ['CHEESE_SMTP_USE_SSL'])
MAIL_USE_TLS                     = int(os.environ['CHEESE_SMTP_USE_TLS'])
# MySQL
MYSQL_HOST                       = os.environ['CHEESE_MYSQL_HOST']
MYSQL_DATABASE                   = os.environ['CHEESE_MYSQL_DATABASE']
MYSQL_USER                       = os.environ['CHEESE_MYSQL_USER']
MYSQL_PASSWORD                   = os.environ['CHEESE_MYSQL_PASSWORD']
SQLALCHEMY_TRACK_MODIFICATIONS = False
if DEBUG:
    # Settings for testing.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    WTF_CSRF_ENABLED = False
else:
    # Settings for deployment.
    SQLALCHEMY_DATABASE_URI = \
        'mysql://'+MYSQL_USER+':'+MYSQL_PASSWORD \
            +'@'+MYSQL_HOST+'/'+MYSQL_DATABASE
    # Make sure MySQL connections are recycled (in wait_timeout period).
    # See https://stackoverflow.com/questions/19052973/operationalerror-mysql-connection-not-available
    SQLALCHEMY_POOL_RECYCLE = 500
# Flask-WTF
RECAPTCHA_PUBLIC_KEY  = os.environ['CHEESE_RECAPTCHA_PUBLIC_KEY']
RECAPTCHA_PRIVATE_KEY = os.environ['CHEESE_RECAPTCHA_PRIVATE_KEY']
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
USER_AFTER_LOGIN_ENDPOINT   = 'cheese.index'
USER_AFTER_LOGOUT_ENDPOINT  = 'cheese.index'
# Constants
PAGE_TITLE = 'The C.H.E.E.S.E. Project CIC'
PHASE_START_DATES = [datetime.date(2015, 4, 15),
                     datetime.date(2016, 4, 15),
                     datetime.date(2017, 4, 15),
                     datetime.date(2018, 4, 15),
                     datetime.date(2019, 4, 15),
                     datetime.date(2020, 4, 15),
                     datetime.date(2021, 4, 15)]
NUM_PHASES = len(PHASE_START_DATES)
ONE_MONTH_FOLLOW_UP_DAYS = 31
ONE_YEAR_FOLLOW_UP_DAYS = 365.25
START_PHASE_NEW_SURVEY_FORMS = 5
