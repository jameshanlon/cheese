import os
from flask import Flask
import flask_admin as admin
from flask_flatpages import FlatPages
from flask_mail import Mail
from flask_migrate import Migrate, MigrateCommand
from flask_uploads import UploadSet, configure_uploads, patch_request_class, \
                          IMAGES
from flask_thumbnails import Thumbnail
from flask_user import SQLAlchemyAdapter, UserManager
from flask_script import Command, Manager, Server
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from jinja2 import Markup
from mixer.backend.flask import mixer

# Global declarations since they are imported by manage.py
app = Flask(__name__)
app.config.from_object('cheese.settings')
db = SQLAlchemy(app)
manager = Manager(app)

def init_email_error_handler(app):
    if app.debug:
        return
    # Setup an SMTP mail handler for error-level messages
    # Log errors using: app.logger.error('Some error message')
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler(
        mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
        fromaddr=app.config['MAIL_DEFAULT_SENDER'],
        toaddrs=app.config['ADMINS'],
        subject=app.config['SYSTEM_ERROR_SUBJECT_LINE'],
        credentials=(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']),
        secure=() if app.config.get('MAIL_USE_TLS') else None, )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

def init_admin(app):
    from cheese.models import User, UserInvitation, Role, Surveys, Results, \
                              MonthFeedback, YearFeedback, Inventory, Kits, \
                              ThermalImage
    from cheese.views import CheeseAdminIndexView, AdminModelView, UserView, \
                             SurveysView, ResultsView, MonthFeedbackView, \
                             YearFeedbackView, InventoryView, KitsView, \
                             ThermalImageView
    global admin
    admin = admin.Admin(app, name='CHEESE database',
                        index_view=CheeseAdminIndexView(name='Overview'),
                        base_template='admin_master.html',
                        template_mode='bootstrap3')
    admin.add_view(UserView(User, db.session,
                            name='Users'))
    admin.add_view(AdminModelView(UserInvitation, db.session,
                                  name='Invitations'))
    admin.add_view(AdminModelView(Role, db.session,
                                  name='Roles'))
    admin.add_view(SurveysView(Surveys, db.session))
    admin.add_view(ResultsView(Results, db.session))
    admin.add_view(MonthFeedbackView(MonthFeedback, db.session,
                                     name='1 month feedback'))
    admin.add_view(YearFeedbackView(YearFeedback, db.session,
                                    name='1 year feedback'))
    admin.add_view(InventoryView(Inventory, db.session))
    admin.add_view(KitsView(Kits, db.session))
    admin.add_view(ThermalImageView(ThermalImage, db.session,
                                    name='Thermal images'))

def init_app(app):
    global mail
    global user_manager
    global images
    global pages
    mail = Mail(app)
    CSRFProtect(app)
    migrate = Migrate(app, db, compare_type=True)
    pages = FlatPages(app)
    thumb = Thumbnail(app)
    images = UploadSet('images', list(IMAGES)+[x.upper() for x in IMAGES])
    configure_uploads(app, images)
    patch_request_class(app, app.config['MAX_IMAGE_SIZE'])
    mixer.init_app(app)
    # Setup Flask-User
    from cheese.models import User, UserInvitation
    db_adapter = SQLAlchemyAdapter(db, User, UserInvitationClass=UserInvitation)
    user_manager = UserManager(db_adapter, app)
    # Other initialisation.
    init_admin(app)
    init_email_error_handler(app)
    # Manager commands.
    manager.add_command('db', MigrateCommand)
    manager.add_command('runserver', Server(host='0.0.0.0',
                                            passthrough_errors=False))
    import cheese.commands
    import cheese.filters
    import cheese.signals
