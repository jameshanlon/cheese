import datetime
import os
import sys
import re
import random
import string
from functools import wraps
from flask import Flask, url_for, redirect, render_template, \
                  render_template_string, request, flash, \
                  Response
import flask_admin as admin
import flask_login as login
from flask_admin.contrib import sqla
from flask_admin import helpers, expose
from flask_admin import form as admin_form
from flask_basicauth import BasicAuth
from flask_flatpages import FlatPages
from flask_migrate import Migrate, MigrateCommand
from flask_uploads import UploadSet, configure_uploads, patch_request_class, \
                          IMAGES, UploadNotAllowed
from flask_thumbnails import Thumbnail
from flask_script import Command, Manager, Server
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.event import listens_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import Form, FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from jinja2 import Markup
from wtforms import form, fields, validators
from wtforms.fields.html5 import EmailField, DateField
from wtforms_sqlalchemy.orm import model_form
from models import *

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

# Configuration parameters.
MYSQL_HOST     = os.environ['CHEESE_MYSQL_HOST']
MYSQL_DATABASE = os.environ['CHEESE_MYSQL_DATABASE']
MYSQL_USER     = os.environ['CHEESE_MYSQL_USER']
MYSQL_PASSWORD = os.environ['CHEESE_MYSQL_PASSWORD']
SMTP_SERVER    = os.environ['CHEESE_SMTP_SERVER']
SMTP_USERNAME  = os.environ['CHEESE_SMTP_USERNAME']
SMTP_PASSWORD  = os.environ['CHEESE_SMTP_PASSWORD']
EMAIL_SENDER   = os.environ['CHEESE_EMAIL_SENDER']
EMAIL_RECEIVER = os.environ['CHEESE_EMAIL_RECEIVER']
AUTH_USER      = os.environ['CHEESE_AUTH_USER']
AUTH_PASSWORD  = os.environ['CHEESE_AUTH_PASSWORD']

# Init Flask and extensions.
app = Flask(__name__)
app.config.from_pyfile('settings.cfg')
app.config['SECRET_KEY'] = os.environ['CHEESE_SECRET_KEY']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if 'CHEESE_SQLITE' in os.environ:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = \
        'mysql://'+MYSQL_USER+':'+MYSQL_PASSWORD \
            +'@'+MYSQL_HOST+'/'+MYSQL_DATABASE
app.debug = True
db = SQLAlchemy(app)
migrate = Migrate(app, db, compare_type=True)
manager = Manager(app)
basic_auth = BasicAuth(app)
login_manager = login.LoginManager()
login_manager.init_app(app)
pages = FlatPages(app)
thumb = Thumbnail(app)
images = UploadSet('images', IMAGES+[x.upper() for x in IMAGES])
configure_uploads(app, images)
patch_request_class(app, 4 * 1024 * 1024)

def choice(string):
    return (string, string)


def random_string(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) \
                for _ in range(length))


WARDS = [
    'Bishopston',
    'Cotham',
    'Easton',
    'Filwood (Knowle West)',
    'Lawrence Weston',
    'Redland',
    'Other', ]
BUILDING_TYPES = [
    'Flat',
    'Maisonette',
    'Mid terrace',
    'End terrace',
    'Semi-detatched',
    'Detatched',
    'Other', ]
WALL_CONSTRUCTION_TYPES = [
    'Solid brick',
    'Insulated cavity',
    'Uninsulated cavity',
    'Stone',
    'Timber',
    'Other', ]
OCCUPATION_TYPES = [
    'Owned',
    'Rented privately',
    'Rented council',
    'Rented housing association',
    'Other', ]

#===-----------------------------------------------------------------------===#
# Models.
#===-----------------------------------------------------------------------===#

class People(db.Model):
    groups = ['Admin', 'Management', 'Coordinator', 'Surveyor']
    id = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120))
    password   = db.Column(db.String(128))
    first_name = db.Column(db.String(100))
    last_name  = db.Column(db.String(100))
    group      = db.Column(db.Enum(*groups), nullable=False)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __unicode__(self):
        return self.email


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name                = db.Column(db.String(200))
    asset_number        = db.Column(db.Integer, unique=True)
    serial_number       = db.Column(db.String(50), unique=True)
    date_of_purchase    = db.Column(db.Date)
    value               = db.Column(db.Float)
    sim_iccid           = db.Column(db.String(25), unique=True)
    imei                = db.Column(db.String(25), unique=True)
    phone_number        = db.Column(db.String(20), unique=True)
    icloud_username     = db.Column(db.String(25))
    icloud_password     = db.Column(db.String(25))
    credit_amount       = db.Column(db.Float)
    credit_date         = db.Column(db.Date())
    notes               = db.Column(db.Text())
    # Kit
    kit_id = db.Column(db.Integer, db.ForeignKey('kits.id'))
    kit    = db.relationship('Kits')

    def __repr__(self):
        return self.name+' (#'+str(self.asset_number)+')'


class Kits(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(200))
    notes        = db.Column(db.Text())
    # Inventory
    inventory  = db.relationship('Inventory')

    def __repr__(self):
        if self.name:
            return self.name
        return 'Unnamed kit '+str(self.id)


class Surveys(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name                      = db.Column(db.String(100))
    address_line              = db.Column(db.String(100))
    postcode                  = db.Column(db.String(10))
    ward                      = db.Column(db.String(50))
    email                     = db.Column(db.String(100))
    telephone                 = db.Column(db.String(20))
    reference                 = db.Column(db.String(8))
    survey_request_date       = db.Column(db.Date,
                                  default=datetime.datetime.now().date())
    building_type             = db.Column(db.Enum(*BUILDING_TYPES))
    num_main_rooms            = db.Column(db.Integer)
    can_heat_comfortably      = db.Column(db.Boolean, default=False)
    expected_benefit          = db.Column(db.Text)
    referral                  = db.Column(db.String(100))
    availability              = db.Column(db.Text)
    free_survey_consideration = db.Column(db.Boolean, default=False)
    fee                       = db.Column(db.Float)
    fee_paid                  = db.Column(db.Boolean, default=False)
    fee_paid_date             = db.Column(db.Date)
    survey_date               = db.Column(db.DateTime)
    survey_complete           = db.Column(db.Boolean, default=False)
    followed_up               = db.Column(db.Boolean, default=False)
    notes                      = db.Column(db.Text)

    def __repr__(self):
        if self.reference:
            return self.reference
        elif self.name and self.address_line:
            return self.name+', '+self.address_line
        elif self.name:
            return self.name
        elif self.address_line:
            return self.address_line
        return 'Survey '+str(self.id)

class Results(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date                       = db.Column(db.DateTime,
                                           default=datetime.datetime.now())
    surveyors_name             = db.Column(db.String(50))
    householders_name          = db.Column(db.String(50))
    address_line               = db.Column(db.String(100))
    survey_date                = db.Column(db.Date)
    external_temperature       = db.Column(db.Float)
    loaned_cheese_box          = db.Column(db.Boolean, default=False)
    cheese_box_number          = db.Column(db.String(25))
    building_type              = db.Column(db.Enum(*BUILDING_TYPES))
    year_of_construction       = db.Column(db.Integer)
    wall_construction          = db.Column(db.Enum(*WALL_CONSTRUCTION_TYPES))
    occupation_type            = db.Column(db.Enum(*OCCUPATION_TYPES))
    primary_heating_type       = db.Column(db.String(150))
    secondary_heating_type     = db.Column(db.String(150))
    depth_loft_insulation      = db.Column(db.String(150))
    number_open_fireplaces     = db.Column(db.String(150))
    double_glazing             = db.Column(db.String(150))
    num_occupants              = db.Column(db.Integer)
    annual_gas_kwh             = db.Column(db.Float)
    annual_elec_kwh            = db.Column(db.Float)
    annual_solid_spend         = db.Column(db.Float)
    renewable_contribution_kwh = db.Column(db.Float)
    faults_identified          = db.Column(db.Text)
    recommendations            = db.Column(db.Text)
    notes                      = db.Column(db.Text)
    # Survey ref
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'))
    survey    = db.relationship('Surveys')

    def __repr__(self):
        return '<Result '+str(self.id)+'>'


class MonthFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date                  = db.Column(db.DateTime,
                                      default=datetime.datetime.now())
    householders_name     = db.Column(db.String(50))
    address               = db.Column(db.String(100))
    annual_gas_kwh        = db.Column(db.Float)
    annual_elec_kwh       = db.Column(db.Float)
    annual_solid_spend    = db.Column(db.Float)
    renewable_contrib_kwh = db.Column(db.Float)
    planned_actions       = db.Column(db.Text)
    feedback              = db.Column(db.Text)
    notes                 = db.Column(db.Text)
    # Survey ref
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'))
    survey    = db.relationship('Surveys')

    def __repr__(self):
        return '<Month feedback '+str(self.id)+'>'


class YearFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date                  = db.Column(db.DateTime,
                                      default=datetime.datetime.now())
    householders_name     = db.Column(db.String(50))
    address               = db.Column(db.String(100))
    annual_gas_kwh        = db.Column(db.Float)
    annual_elec_kwh       = db.Column(db.Float)
    annual_solid_spend    = db.Column(db.Float)
    renewable_contrib_kwh = db.Column(db.Float)
    diy_work              = db.Column(db.Text)
    prof_work             = db.Column(db.Text)
    contractors_used      = db.Column(db.Text)
    total_spent           = db.Column(db.Float)
    planned_work          = db.Column(db.Text)
    wellbeing_improvement = db.Column(db.Text)
    behaviour_changes     = db.Column(db.Text)
    feedback              = db.Column(db.Text)
    notes                 = db.Column(db.Text)
    # Survey ref
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'))
    survey    = db.relationship('Surveys')

    def __repr__(self):
        return '<Year feedback '+str(self.id)+'>'


class ThermalImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename     = db.Column(db.Unicode(100))
    description  = db.Column(db.UnicodeText)
    submitted_by = db.Column(db.Unicode(50))
    date         = db.Column(db.DateTime,
                             default=datetime.datetime.now())

    def __repr__(self):
        return '<Thermal image '+filename+'>'


#===-----------------------------------------------------------------------===#
# Admin login and views.
#===-----------------------------------------------------------------------===#

# Create user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.session.query(People).get(user_id)


class LoginForm(form.Form):
    email = fields.StringField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()
        if user is None:
            raise validators.ValidationError('Invalid user')
        # Compare plaintext password with the the hash from db.
        if not check_password_hash(user.password, self.password.data):
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return db.session.query(People).filter_by(email=self.email.data).first()


class AdminModelView(sqla.ModelView):
    page_size = 100
    can_export = True
    can_view_details = True
    def is_accessible(self):
        return login.current_user.is_authenticated \
                and login.current_user.group == 'Admin'


class RegularModelView(sqla.ModelView):
    page_size = 100
    can_export = True
    can_view_details = True
    def is_accessible(self):
        return login.current_user.is_authenticated


class CheeseAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(CheeseAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            if user is None:
                flash('Your email was not recognised.')
                return redirect(url_for('.login_view'))
            login.login_user(user)
        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        return super(CheeseAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


class CreateUserForm(form.Form):
    email = fields.StringField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])
    first_name = fields.StringField(validators=[validators.required()])
    last_name = fields.StringField(validators=[validators.required()])
    group = fields.SelectField('Group', choices=[
                    choice('Admin'),
                    choice('Management'),
                    choice('Coordinator'),
                    choice('Surveyor')],
                validators=[validators.required()])


class PeopleView(AdminModelView):
    column_exclude_list = [ 'password' ]
    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        form = CreateUserForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = People()
            form.populate_obj(user)
            user.password = generate_password_hash(form.password.data)
            db.session.add(user)
            db.session.commit()
            login.login_user(user)
            return redirect(url_for('.index_view'))
        return self.render('admin/create_user.html', form=form)


class SurveysView(RegularModelView):
    all_cols = set([
        'name',
        'address_line',
        'postcode',
        'ward',
        'email',
        'telephone',
        'reference',
        'survey_request_date',
        'building_type',
        'num_main_rooms',
        'can_heat_comfortably',
        'expected_benefit',
        'referral',
        'availability',
        'free_survey_consideration',
        'fee',
        'fee_paid',
        'fee_paid_date',
        'survey_date',
        'survey_complete',
        'followed_up',
        'notes', ])
    columns_list = [
        'name',
        'ward',
        'reference',
        'survey_request_date',
        'fee',
        'survey_date',
        'survey_complete',
        'followed_up', ]
    column_filters = columns_list
    column_exclude_list = list(all_cols - set(columns_list))
    form_args = {
        'referral':       { 'label': 'Referral from?' },
        'num_main_rooms': { 'label': 'Number of main rooms' }, }


class ResultsView(RegularModelView):
    all_cols = set([
        'date',
        'surveyors_name',
        'householders_name',
        'address_line',
        'survey_date',
        'external_temperature',
        'cheese_box_loaned',
        'cheese_box_number',
        'building_type',
        'year_of_construction',
        'wall_construction',
        'occupation_type',
        'primary_heating_type',
        'secondary_heating_type',
        'depth_loft_insulation',
        'number_open_fireplaces',
        'double_glazing',
        'num_occupants',
        'annual_gas_kwh',
        'annual_elec_kwh',
        'annual_solid_spend',
        'renewable_contribution_kwh',
        'faults_identified',
        'recommendations',
        'notes',
        'survey', ])
    columns_list = [
        'surveyors_name',
        'householders_name',
        'address_line',
        'survey_date',
        'survey', ]
    column_filters = columns_list
    column_exclude_list = list(all_cols - set(columns_list))
    form_widget_args = {
        'faults_identified': { 'rows': 8, 'cols': 20 },
        'recommendations':   { 'rows': 8, 'cols': 20 },
        'notes':             { 'rows': 8, 'cols': 20 }, }


class MonthFeedbackView(RegularModelView):
    column_exclude_list = [
        'date',
        'annual_gas_kwh',
        'annual_elec_kwh',
        'annual_solid_spend',
        'renewable_contrib_kwh',
        'planned_actions',
        'feedback',
        'notes', ]


class YearFeedbackView(RegularModelView):
    column_exclude_list = [
        'date',
        'annual_gas_kwh',
        'annual_elec_kwh',
        'annual_solid_spend',
        'renewable_contrib_kwh',
        'diy_work',
        'prof_work',
        'total_spent',
        'planned_work',
        'behaviour_changes',
        'feedback',
        'notes', ]


class InventoryView(AdminModelView):
    form_columns = [
            'name',
            'asset_number',
            'serial_number',
            'date_of_purchase',
            'value',
            'sim_iccid',
            'imei',
            'phone_number',
            'icloud_username',
            'icloud_password',
            'credit_amount',
            'credit_date',
            'notes',
            'kit']
    column_list = ['name', 'asset_number', 'kit']
    column_filters = form_columns


class KitsView(AdminModelView):
    form_columns = ['name', 'notes', 'inventory']
    column_list = form_columns
    column_filters = column_list


@listens_for(ThermalImage, 'after_delete')
def del_thermal_image(mapper, connection, target):
    if target.filename:
        try:
	    filename = os.path.join(app.config['UPLOADED_IMAGES_DEST'],
                                    target.filename)
            os.remove(filename)
        except OSError:
            pass


class ThermalImageView(RegularModelView):
    can_create = False
    def _list_thumbnail(view, context, model, name):
        if not model.filename:
            return ''
        filename = os.path.join(app.config['UPLOADED_IMAGES_DEST'],
                                model.filename)
        thumb_filename = thumb.thumbnail(filename, '100x100')
        return Markup('<a href="/{}"><img src="{}"></a>'.format(filename,
                                                                thumb_filename))
    column_formatters = { 'filename': _list_thumbnail, }
    column_exclude_list = ['date', ]


# Setup admin.
admin = admin.Admin(app, name='CHEESE database',
                    index_view=CheeseAdminIndexView(),
                    base_template='admin_master.html')
admin.add_view(PeopleView(People, db.session))
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


#===-----------------------------------------------------------------------===#
# Restricted pages.
#===-----------------------------------------------------------------------===#

def check_auth(username, password):
    return username == AUTH_USER and password == AUTH_PASSWORD


def authenticate():
    return Response('Invalid login.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/submit-results', methods=['GET', 'POST'])
@requires_auth
def submit_results():
    ResultsForm = model_form(Results, db_session=db.session, field_args={
        "surveyors_name":             { "label": "Surveyor's name", },
        "householders_name":          { "label": "Householder's name", },
        "address_line":               { "label": "Address line", },
        "survey_date":                { "label": "Survey date (dd-mm-yyyy)",
                                        "format": "%d-%m-%Y", },
        "external_temperature":       { "label": "External temperature (C)", },
        "loaned_cheese_box":          { "label": "CHEESE box loaned?", },
        "cheese_box_number":          { "label": "CHEESE box number", },
        "building_type" :             { "label": "Building type", },
        "year_of_construction":       { "label": "Year of construction", },
        "wall_construction":          { "label": "Wall construction", },
        "occupation_type":            { "label": "Occupation type", },
        "primary_heating_type":       { "label": "Primary heating type", },
        "secondary_heating_type":     { "label": "Secondary heating type", },
        "depth_loft_insulation":      { "label": "Depth of loft insulation (mm)", },
        "number_open_fireplaces":     { "label": "Number of open fireplaces", },
        "double_glazing":             { "label": "Amount of double glazing", },
        "num_occupants":              { "label": "Number of occupants", },
        "annual_gas_kwh":             { "label": "Annual gas consumption (kWh)", },
        "annual_elec_kwh":            { "label": "Annual electricity consumption (kWh)", },
        "annual_solid_spend":         { "label": "Annual spend on solid fuels (&pound;)", },
        "renewable_contribution_kwh": { "label":"Annual contribution from renewable generation (kWh)", },
        "faults_identified":          { "label": "Faults identified", },
        })
    results = Results()
    results_form = ResultsForm(obj=results)
    form = ResultsForm(request.form, results)
    if request.method=='POST' and helpers.validate_form_on_submit(form):
        form.populate_obj(results)
        db.session.add(results)
        db.session.commit()
        flash('Survey result submitted successfully.')
        return redirect(url_for('submit_results'))
    return render_template('submit-results.html', form=form)


class UploadThermalImageForm(FlaskForm):
    image = FileField('Image file',
              validators=[FileRequired(),
                          FileAllowed(images, 'Only images can be uploaded')])
    description = fields.TextAreaField('Description of the image',
                    validators=[validators.required()])
    submitted_by = fields.StringField('Your name',
                     validators=[validators.required()])


@app.route('/upload-thermal-image', methods=['GET', 'POST'])
@requires_auth
def upload_thermal_image():
    form = UploadThermalImageForm()
    if request.method=='POST' and form.validate_on_submit():
        image = request.files.get('image')
        description = request.form.get('description')
        submitted_by = request.form.get('submitted_by')
        try:
            filename = random_string(10)+'_'+image.filename
            filename = images.save(image, name=filename)
        except UploadNotAllowed:
            flash('The uploaded file is not allowed')
        else:
            thermal_image = ThermalImage()
            thermal_image.filename=filename
            thermal_image.description=description
            thermal_image.submitted_by=submitted_by
            db.session.add(thermal_image)
            db.session.commit()
            flash('The thermal image has been submitted successfully.')
            form = UploadThermalImageForm()
    return render_template('upload-thermal-image.html', form=form)


@app.route('/collected-thermal-images')
@requires_auth
def collected_thermal_images():
    return render_template('collected-thermal-images.html',
                           images=ThermalImage.query.all())


#===-----------------------------------------------------------------------===#
# Website pages.
#===-----------------------------------------------------------------------===#

def send_email(recipient, subject, message):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(message))
    mailserver = smtplib.SMTP(SMTP_SERVER, 587)
    mailserver.ehlo()
    mailserver.starttls()
    mailserver.ehlo()
    mailserver.login(SMTP_USERNAME, SMTP_PASSWORD)
    mailserver.sendmail(EMAIL_SENDER, recipient, msg.as_string())
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


class ApplySurveyForm(form.Form):
    name = fields.StringField(validators=[validators.required()])
    address_line = fields.StringField(validators=[validators.required()])
    postcode = fields.StringField(validators=[validators.required()])
    ward = fields.SelectField('Ward',
               choices=[choice('')]+[choice(x) for x in WARDS],
               default='', validators=[validators.required()],)
    email = EmailField(validators=[validators.required(),
                                   validators.Email()])
    telephone = fields.StringField(validators=[validators.required()])
    availability = fields.TextAreaField(validators=[validators.required()])
    building_type = fields.SelectField('Building type',
            choices=[choice('')]+[choice(x) for x in BUILDING_TYPES],
            default='', validators=[validators.required()])
    num_main_rooms = fields.IntegerField('Number of main rooms ' \
                                         +'(reception + living + bedroom)')
    can_heat_comfortably = \
        fields.BooleanField('Can you heat your home to a comfortable ' \
                            +'temperature in the winter?')
    expected_benefit = fields.TextAreaField('How do you think you will ' \
                                            + 'benefit from a survey?',
                                        validators=[validators.required()])
    referral = fields.StringField('How did you hear about CHEESE?',
                                  validators=[validators.required()])
    free_survey_consideration = \
        fields.BooleanField('I live in a low-income household and ' \
            +'would like to be considered for a free survey.')
    agree_to_requirements = \
        fields.BooleanField('I agree to make the  ' \
            +'<a href="/pre-survey-guide#preparation" target="_blank">'
            +'necessary preparations</a> for the survey and am happy ' \
            +'to <a href="/pre-survey-guide#follow-ups" target="_blank"> ' \
            +'report my progress after one month and one year</a>.',
            validators=[validators.required()])


@app.route('/apply-for-a-survey', methods=['GET', 'POST'])
def apply_for_a_survey():
    form = ApplySurveyForm(request.form)
    if request.method=='POST' and helpers.validate_form_on_submit(form):
        # Add to db.
        survey = Surveys()
        form.populate_obj(survey)
        db.session.add(survey)
        db.session.commit()
        # Send email to applicant.
        subject = 'Request for a CHEESE survey'
        message =  'Dear '+form.name.data+',\n\n'
        message += 'Thank you for your survey request.\n\n'
        message += 'We will be in touch soon when we have some prospective '
        message += 'dates for the survey.\n\n'
        message += 'In the mean time, please get in touch if you have any '
        message += 'questions.\n\n'
        message += 'Many thanks,\nThe CHEESE Project team\n\n'
        message += 'www.cheeseproject.co.uk\ninfo@cheeseproject.co.uk'
        send_email(form.email.data, subject, message)
        # Send admin email.
        subject = 'New request for a CHEESE survey'
        message = 'From '+form.name.data+', '+form.address_line.data \
                  + ' at '+str(datetime.datetime.today())
        send_email(EMAIL_RECEIVER, subject, message)
        # Success page.
        page = pages.get('application-successful')
        return render_template('page.html', page=page)
    return render_template('apply-for-a-survey.html', form=form)


@app.route('/one-month-feedback', methods=['GET', 'POST'])
def one_month_feedback():
    not_needed = 'We only need this if we didn\'t collect this during the survey.'
    kwh_help = 'For help with calculating the value, please see ' \
                +'<a href="/cheese-box#recording-energy-use">our guide</a>.' \
                +'<br>'+not_needed
    MonthFeedbackForm = model_form(MonthFeedback, db_session=db.session,
        exclude=['survey', 'notes'],
	field_args={
          'householders_name': {
	    'label': 'Name',
            'validators': [validators.required()], },
          'address': {
	       'label': 'Address',
               'validators': [validators.required()], },
          'annual_gas_kwh': {
              'label': 'Total annual gas usage in kWh',
              'description': kwh_help, },
          'annual_elec_kwh': {
              'label': 'Total annual electricity usage in kWh',
              'description': kwh_help, },
 	  'annual_solid_spend': {
              'label': 'Total annual spend in pounds (&pound;) on solid fuels',
              'description': 'Such as wood, coal etc.<br>'+not_needed, },
          'renewable_contrib_kwh': {
              'label': 'Total annual contribution of any renewable generation in kWh',
              'description': 'Such as from solar PV or a ground-source heat pump.<br>'+not_needed, },
	  'planned_actions': {
              'label': 'What you are planning to do to improve the thermal efficiency of your home?',
              'description': 'This can be anything from draught proofing to installing external wall insulation.',
	      'validators': [validators.required()], },
	  'feedback': {
              'label': 'Do you have any feedback you have on your CHEESE survey?',
              'description': 'We would like to hear what you think about:'
                              +' the organisation of the survey,'
                              +' the conduct of the Energy Tracers,'
                              +' the results of the survey and suggested remedies,'
                              +' the usefulness of the <a href="/cheese-box">CHEESE box</a>,'
                              +' the overall value for money of the survey,'
                              +' your overall satisfaction,'
                              +' and anything else at all you would like to let us know.', },
          }
        )
    follow_up = MonthFeedback()
    form = MonthFeedbackForm(request.form, follow_up)
    if request.method=='POST' and helpers.validate_form_on_submit(form):
        form.populate_obj(follow_up)
        db.session.add(follow_up)
        db.session.commit()
        # Send admin email.
        subject = 'New one year response'
        message = 'From '+form.name.data+', '+form.address_line.data \
                  + ' at '+str(datetime.datetime.today())
        send_email(EMAIL_RECEIVER, subject, message)
        # Flash success message.
        flash('Your one month feedback was submitted successfully, thank you.')
        return redirect(url_for('one_month_feedback'))
    return render_template('one-month-feedback.html', form=form)


@app.route('/one-year-feedback', methods=['GET', 'POST'])
def one_year_feedback():
    kwh_help = 'For your usage in the year immediately after your survey.<br>' \
                +'For help with calculating the value, please see ' \
                +'<a href="/cheese-box#recording-energy-use">our guide</a>.'
    YearFeedbackForm = model_form(YearFeedback, db_session=db.session,
        exclude=['survey', 'notes'],
	field_args={
          'householders_name': {
              'label': 'Name',
	      'validators': [validators.required()], },
          'address': {
              'label': 'Address',
	      'validators': [validators.required()], },
          'annual_gas_kwh': {
              'label': 'Total annual gas usage in kWh',
              'description': kwh_help,
              'validators': [validators.required()], },
          'annual_elec_kwh': {
              'label': 'Total annual electricity usage in kWh',
              'description': kwh_help,
              'validators': [validators.required()], },
 	  'annual_solid_spend': {
              'label': 'Total annual spend in pounds (&pound;) on solid fuels',
              'description': 'Such as wood, coal etc.',
              'validators': [validators.required()], },
          'renewable_contrib_kwh': {
              'label': 'Total annual contribution of any renewable generation in kWh',
              'description': 'Such as from solar PV or a ground-source heat pump.',
              'validators': [validators.required()], },
          'diy_work' : {
              'label': 'What work have you done yourself?',
	      'validators': [validators.required()], },
          'prof_work': {
              'label': 'What work have you paid for to be done professionally?',
	      'validators': [validators.required()], },
          'contractors_used': {
              'label': 'If you had work done professionally, which contractors did you use?',
              'description': 'And were these contractors based in Bristol or from further afield?', },
          'total_spent': {
	      'label': 'Approximately how much have you spent in total on energy improvements to your home?',
              'description': 'Only answer this if you feel comfortable to.', },
          'planned_work': {
	      'label': 'Do you have any further work planned? And, if so, what?',
	      'validators': [validators.required()], },
          'wellbeing_improvement': {
              'label': 'Do you now feel you have a warmer home?',
              'description': 'Perhaps even if you haven\'t saved any money on your bills!', },
          'behaviour_changes': {
              'label': 'Do you think your behaviour has changed at all after having had the survey? And, if so, how?',
              'description': 'Such as the period and temperature you use the heating for, or the way you use the space in your home.',
              'validators': [validators.required()], },
	  'feedback':
            { 'label': 'Do you have any feedback you have on the CHEESE Project?',
              'description': 'We would like to hear what you think about:'
                              +' how useful the survey was,'
                              +' how useful the <a href="/cheese-box">CHEESE box</a> was,'
                              +' your overall satisfaction,'
                              +' and anything else at all you would like to let us know.', },
          }
        )
    follow_up = YearFeedback()
    form = YearFeedbackForm(request.form, follow_up)
    if request.method=='POST' and helpers.validate_form_on_submit(form):
        form.populate_obj(follow_up)
        db.session.add(follow_up)
        db.session.commit()
        # Send admin email.
        subject = 'New one year response'
        message = 'From '+form.name.data+', '+form.address_line.data \
                  + ' at '+str(datetime.datetime.today())
        send_email(EMAIL_RECEIVER, subject, message)
        # Flash success message.
        flash('Your one year feedback was submitted successfully, thank you.')
        return redirect(url_for('one_year_feedback'))
    return render_template('one-year-feedback.html', form=form)



@app.route('/')
def index():
    news_items = get_news()
    if len(news_items) >= 3:
        news_items = news_items[:3]
    return render_template('index.html', news_items=news_items)


@app.route('/news')
def news():
    return render_template('news.html', news_items=get_news())


# Any flat pages.
@app.route('/<path:path>')
def page(path):
    page = pages.get_or_404(path)
    template = page.meta.get('template', 'page.html')
    return render_template(template, page=page)


@app.route('/home-surveys')
def home_surveys():
    # Flat page with template code.
    page = pages.get('home-surveys')
    page.html = render_template_string(page.html)
    template = page.meta.get('template', 'page.html')
    return render_template(template, page=page)


@app.route('/cheese-box')
def cheese_box():
    # Flat page with template code.
    page = pages.get('cheese-box')
    page.html = render_template_string(page.html)
    template = page.meta.get('template', 'page.html')
    return render_template(template, page=page)


@manager.command
def populate_db():
    "Create a test database"
    db.drop_all()
    db.create_all()
    admin_user = People(email="admin",
                        password=generate_password_hash("admin"),
                        group='Admin')
    db.session.add(admin_user)
    db.session.commit()


#===-----------------------------------------------------------------------===#
# On the command line.
#===-----------------------------------------------------------------------===#

manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Server(host='0.0.0.0',
                                        passthrough_errors=False))

if __name__ == '__main__':
    manager.run()
