import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask import Flask
import flask_admin
from flask_uploads import configure_uploads, patch_request_class
from flask_wtf.csrf import CSRFProtect
from mixer.backend.flask import mixer

def init_signals(app):
    # Can't do this with Blueprints, so reference app here.
    from flask_user import user_registered, \
                           user_changed_password, \
                           user_changed_username, \
                           user_confirmed_email, \
                           user_forgot_password, \
                           user_logged_in, \
                           user_logged_out, \
                           user_reset_password
    from cheese.views import user_registered_hook, \
                             user_changed_password_hook, \
                             user_changed_username_hook, \
                             user_confirmed_email_hook, \
                             user_forgot_password_hook, \
                             user_logged_in_hook, \
                             user_logged_out_hook, \
                             user_reset_password_hook
    user_registered_hook       = user_registered.connect_via(app)(user_registered_hook)
    user_confirmed_email_hook  = user_confirmed_email.connect_via(app)(user_confirmed_email_hook)
    user_changed_password_hook = user_changed_password.connect_via(app)(user_changed_password_hook)
    user_changed_username_hook = user_changed_username.connect_via(app)(user_changed_username_hook)
    user_forgot_password_hook  = user_forgot_password.connect_via(app)(user_forgot_password_hook)
    user_reset_password_hook   = user_reset_password.connect_via(app)(user_reset_password_hook)
    user_logged_in_hook        = user_logged_in.connect_via(app)(user_logged_in_hook)
    user_logged_out_hook       = user_logged_out.connect_via(app)(user_logged_out_hook)

def init_file_logging(app):
    # Add a file logging handler.
    file_handler = RotatingFileHandler(app.config['LOG_FILENAME'],
                                       backupCount=10)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

def init_mail_logging(app):
    # Setup an SMTP mail handler for error-level messages
    # Log errors using: app.logger.error('Some error message')
    if app.debug:
        return
    mail_handler = SMTPHandler(
        mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
        fromaddr=app.config['MAIL_DEFAULT_SENDER'],
        toaddrs=app.config['ADMINS'],
        subject='[CHEESE] Website error',
        credentials=(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']),
        secure=() if app.config.get('MAIL_USE_TLS') else None, )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

def create_app(config={}):
    app = Flask(__name__)
    # Config.
    app.config.from_object('cheese.settings')
    app.config.update(config)
    CSRFProtect(app)
    # Blueprints.
    from cheese.views import bp as cheese_bp
    from cheese.filters import bp as filters_bp
    from cheese.functions import bp as functions_bp
    app.register_blueprint(cheese_bp)
    app.register_blueprint(filters_bp)
    app.register_blueprint(functions_bp)
    # Models.
    from cheese.models import db, migrate, user_manager, db_adapter
    db.init_app(app)
    migrate.init_app(app, db)
    user_manager.init_app(app, db_adapter)
    # Admin.
    from cheese.views import init_admin, CheeseAdminIndexView
    admin = flask_admin.Admin(app,
                              name='CHEESE database',
                              index_view=CheeseAdminIndexView(name='Summary'),
                              base_template='admin_master.html',
                              template_mode='bootstrap3')
    init_admin(admin)
    # Flask extensions.
    from cheese.views import mail, images, pages, thumb
    mail.init_app(app)
    pages.init_app(app)
    thumb.init_app(app)
    configure_uploads(app, images)
    patch_request_class(app, app.config['MAX_IMAGE_SIZE'])
    mixer.init_app(app)
    # Register signals.
    init_signals(app)
    # Add logging handlers.
    init_file_logging(app)
    init_mail_logging(app)
    app.logger.setLevel(logging.INFO)
    # Additional CLI commands.
    from cheese.commands import resetdb
    resetdb = app.cli.command('resetdb')(resetdb)
    return app
