import datetime
import os
import sys
import re
from functools import wraps
from flask import Flask, url_for, redirect, render_template, \
                  render_template_string, request, flash, \
                  Response
import flask_admin as admin
import flask_login as login
from flask_admin.contrib import sqla
from flask_admin import helpers, expose
from flask_basicauth import BasicAuth
from flask_flatpages import FlatPages
from flask_migrate import Migrate, MigrateCommand
from flask_thumbnails import Thumbnail
from flask_script import Command, Manager, Server
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import form, fields, validators
from wtforms.fields.html5 import EmailField, DateField
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
migrate = Migrate(app, db)
manager = Manager(app)
basic_auth = BasicAuth(app)
login_manager = login.LoginManager()
login_manager.init_app(app)
pages = FlatPages(app)
thumb = Thumbnail(app)

def choice(string):
    return (string, string)

WARDS = [
    choice('Bishopston'),
    choice('Cotham'),
    choice('Easton'),
    choice('Filwood (Knowle West)'),
    choice('Lawrence Weston'),
    choice('Redland'),
    choice('Other'), ]
BUILDING_TYPES = [
    choice('Flat'),
    choice('Maisonette'),
    choice('Mid terrace'),
    choice('End terrace'),
    choice('Semi-detatched'),
    choice('Detatched'),
    choice('Other'), ]
WALL_CONSTRUCTION_TYPES = [
    choice('Solid brick'),
    choice('Insulated cavity'),
    choice('Uninsulated cavity'),
    choice('Stone'),
    choice('Timber'),
    choice('Other'), ]
OCCUPATION_TYPES = [
    choice('Owned'),
    choice('Rented privately'),
    choice('Rented council'),
    choice('Rented housing association'),
    choice('Other'), ]

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
    # Loan
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'))
    loan    = db.relationship('Loans')
    # Invoice
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    invoice    = db.relationship('Invoices')

    def __repr__(self):
        return self.name+' (#'+str(self.asset_number)+')'


class Kits(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(200))
    notes        = db.Column(db.Text())
    # Inventory
    inventory  = db.relationship('Inventory')
    # Loan
    loan_id    = db.Column(db.Integer, db.ForeignKey('loans.id'))
    loan       = db.relationship('Loans')
    # Invoice
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    invoice    = db.relationship('Invoices')

    def __repr__(self):
        if self.name:
            return self.name
        return 'Unknown loan '+str(self.id)


class Loans(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(100))
    email     = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    date      = db.Column(db.Date(), default=datetime.datetime.now().date())
    notes     = db.Column(db.Text)
    item      = db.relationship('Inventory')
    kit       = db.relationship('Kits')

    def __repr__(self):
        if self.name and self.date:
            return 'To '+self.name+' on '+str(self.date)
        return 'Unknown loan '+str(self.id)


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
    building_type             = db.Column(db.String(25))
    num_main_rooms            = db.Column(db.Integer)
    expected_benefit          = db.Column(db.Text)
    referral                  = db.Column(db.String(100))
    availability              = db.Column(db.Text)
    free_survey_consideration = db.Column(db.Boolean, default=False)
    fee                       = db.Column(db.Float)
    fee_paid                  = db.Column(db.Boolean, default=False)
    fee_paid_date             = db.Column(db.Date)
    survey_date               = db.Column(db.DateTime)
    survey_complete           = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Survey '+str(self.id)+'>'


class Results(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    surveyors_name             = db.Column(db.String(50))
    householders_name          = db.Column(db.String(50))
    address_line               = db.Column(db.String(100))
    survey_date                = db.Column(db.DateTime)
    external_temperature       = db.Column(db.Float)
    cheese_box_number          = db.Column(db.String(25))
    building_type              = db.Column(db.String(30))
    year_of_construction       = db.Column(db.Integer)
    wall_construction          = db.Column(db.String(30))
    occupation_type            = db.Column(db.String(30))
    primary_heating_type       = db.Column(db.String(30))
    secondary_heating_type     = db.Column(db.String(30))
    depth_loft_insulation      = db.Column(db.String(30))
    number_open_fireplaces     = db.Column(db.String(30))
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


class FollowUps(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type                       = db.Column(db.Enum('One month', 'One year'))
    householders_name          = db.Column(db.String(50))
    address_line               = db.Column(db.String(100))
    annual_gas_kwh             = db.Column(db.Float)
    annual_elec_kwh            = db.Column(db.Float)
    annual_solid_spend         = db.Column(db.Float)
    renewable_contribution_kwh = db.Column(db.Float)
    householder_actions        = db.Column(db.Text)
    householder_feedback       = db.Column(db.Text)
    notes                      = db.Column(db.Text)
    # Survey ref
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'))
    survey    = db.relationship('Surveys')

    def __repr__(self):
        return '<Follow up '+str(self.id)+'>'


class Invoices(db.Model):
    categories = [
            'Salaries',
            'NIC',
            'Pension',
            'Fees',
            'License fees',
            'Technical fees',
            'Office',
            'Legal/insurance',
            'Publicity/printing',
            'Training/video',
            'Travel',
            'Segments',
            'Capital kit',
            'Consumables', ]
    id = db.Column(db.Integer, primary_key=True)
    reference    = db.Column(db.String(100))
    amount       = db.Column(db.Float)
    date_raised  = db.Column(db.Date, default=datetime.datetime.now().date())
    paid_by      = db.Column(db.String(100))
    settled      = db.Column(db.Boolean, default=False)
    date_settled = db.Column(db.Date)
    category     = db.Column(db.Enum(*categories))
    notes        = db.Column(db.Text)
    inventory    = db.relationship('Inventory')
    kits         = db.relationship('Kits')

    def __repr__(self):
        return 'Invoice #'+self.id+' raised '+str(self.date_raised)


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
        'expected_benefit',
        'referral',
        'availability',
        'free_survey_consideration',
        'fee',
        'fee_paid',
        'fee_paid_date',
        'survey_date',
        'survey_complete', ])
    columns_list = [
        'name',
        'ward',
        'reference',
        'survey_request_date',
        'fee',
        'survey_date',
        'survey_complete', ]
    column_filters = columns_list
    column_exclude_list = list(all_cols - set(columns_list))
    form_choices = {
        'building_type': BUILDING_TYPES, }
    form_args = {
        'referral':       { 'label': 'Referral from?' },
        'num_main_rooms': { 'label': 'Number of main rooms' }, }


class ResultsView(RegularModelView):
    all_cols = set([
        'surveyors_name',
        'householders_name',
        'address_line',
        'survey_date',
        'external_temperature',
        'cheese_box_number',
        'building_type',
        'year_of_construction',
        'wall_construction',
        'occupation_type',
        'primary_heating_type',
        'secondary_heating_type',
        'depth_loft_insulation',
        'number_open_fireplaces',
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


class FollowUpsView(RegularModelView):
    column_exclude_list = [
        'annual_gas_kwh',
        'annual_elec_kwh',
        'annual_solid_spend',
        'renewable_contribution_kwh',
        'householder_actions',
        'householder_feedback',
        'notes', ]
    form_widget_args = {
        'householder_actions':  { 'rows': 8, 'cols': 20 },
        'householder_feedback': { 'rows': 8, 'cols': 20 },
        'notes':                { 'rows': 8, 'cols': 20 }, }


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
            'kit',
            'invoice']
    column_list = ['name', 'asset_number', 'kit', 'loan', 'invoice']
    column_filters = form_columns + ['loan']


class KitsView(AdminModelView):
    form_columns = ['name', 'notes', 'inventory']
    column_list = form_columns + ['invoice']
    column_filters = column_list


class LoansView(AdminModelView):
    form_columns = [
        'name',
        'email',
        'telephone',
        'date',
        'notes',
        'item',
        'kit']
    form_args = {
        'name': { 'label': 'Person loaned to' },
        'date': { 'label': 'Date of loan' },
        'kit':  { 'label': 'Kit loaned' },
        'item': { 'label': 'Item loaned' },
        }
    column_list = ['name', 'item', 'kit']
    column_filters = form_columns


class InvoicesView(AdminModelView):
    form_columns = [
        'reference',
        'amount',
        'date_raised',
        'paid_by',
        'settled',
        'date_settled',
        'category',
        'notes',
        'inventory',
        'kits', ]
    column_list = [
        'id',
        'reference',
        'amount',
        'date_raised',
        'paid_by',
        'settled',
        'date_settled',
        'category', ]
    column_filters = form_columns


# Setup admin.
admin = admin.Admin(app, name='CHEESE database',
                    index_view=CheeseAdminIndexView(),
                    base_template='admin_master.html')
admin.add_view(PeopleView(People, db.session))
admin.add_view(SurveysView(Surveys, db.session))
admin.add_view(ResultsView(Results, db.session))
admin.add_view(FollowUpsView(FollowUps, db.session))
admin.add_view(InventoryView(Inventory, db.session))
admin.add_view(KitsView(Kits, db.session))
admin.add_view(LoansView(Loans, db.session))
admin.add_view(InvoicesView(Invoices, db.session))


#===-----------------------------------------------------------------------===#
# Restricted pages.
#===-----------------------------------------------------------------------===#

def check_auth(username, password):
    return username == AUTH_USER and password == AUTH_PASSWORD


def authenticate():
    return Response(
	'Invalid login.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


class SubmitResultsForm(form.Form):
    surveyors_name = fields.StringField('Surveyor\'s name',
                                        validators=[validators.required()])
    householders_name = fields.StringField('Householder\'s name',
                                           validators=[validators.required()])
    address_line = fields.StringField('Address line',
                                      validators=[validators.required()])
    survey_date = DateField('Survey date (dd-mm-yyyy)', format='%d-%m-%Y',
                      validators=[validators.required()])
    external_temperature = fields.FloatField('External temperature (C)')
    cheese_box_number = fields.StringField('Loaned CHEESE box number')
    building_type = fields.SelectField('Building type',
                        choices=[choice('')]+BUILDING_TYPES, default='',
                        validators=[validators.required()], )
    year_of_construction = fields.IntegerField('Year of construction')
    wall_construction = fields.SelectField('Wall construction',
                            choices=[choice('')]+WALL_CONSTRUCTION_TYPES,
                            validators=[validators.required()], )
    occupation_type = fields.SelectField('Type of occupation',
                          choices=[choice('')]+OCCUPATION_TYPES,
                          validators=[validators.required()], )
    primary_heating_type = fields.StringField('Type of primary heating',
                                validators=[validators.required()])
    secondary_heating_type = fields.StringField('Type of secondary heating',
                                validators=[validators.required()])
    depth_loft_insulation = fields.StringField('Depth of loft insulation (cm)',
                                validators=[validators.required()])
    number_open_fireplaces = fields.StringField('Number of open fireplaces',
                                validators=[validators.required()])
    num_occupants = fields.IntegerField('Number of occupants')
    annual_gas_kwh = fields.FloatField('Annual gas use (kWh)')
    annual_elec_kwh = fields.FloatField('Annual electricity use (kWh)')
    annual_solid_spend = fields.FloatField('Annual solid fuel spend')
    renewable_contribution_kwh = fields.FloatField(
	                         'Contribution from renewable generaiton (kWh)')
    faults_identified = fields.TextAreaField('Faults identified',
                                             validators=[validators.required()])
    recommendations = fields.TextAreaField(validators=[validators.required()])
    notes = fields.TextAreaField()


@app.route('/submit-results', methods=['GET', 'POST'])
@requires_auth
def submit_results():
    form = SubmitResultsForm(request.form)
    if request.method=='POST' and helpers.validate_form_on_submit(form):
        # Add to db.
        result = Results(
            surveyors_name=form.surveyors_name.data,
            householders_name=form.householders_name.data,
            address_line=form.address_line.data,
            survey_date=form.survey_date.data,
            external_temperature=form.external_temperature.data,
            cheese_box_number=form.cheese_box_number.data,
            building_type=form.building_type.data,
            year_of_construction=form.year_of_construction.data,
            wall_construction=form.wall_construction.data,
            occupation_type=form.occupation_type.data,
            primary_heating_type=form.primary_heating_type.data,
            secondary_heating_type=form.secondary_heating_type.data,
            depth_loft_insulation=form.depth_loft_insulation.data,
            number_open_fireplaces=form.number_open_fireplaces.data,
            num_occupants=form.num_occupants.data,
            annual_gas_kwh=form.annual_gas_kwh.data,
            annual_elec_kwh=form.annual_elec_kwh.data,
            annual_solid_spend=form.annual_solid_spend.data,
            renewable_contribution_kwh=form.renewable_contribution_kwh.data,
            faults_identified=form.faults_identified.data,
            recommendations=form.recommendations.data,
            notes=form.notes.data, )
        db.session.add(result)
        db.session.commit()
        flash('Survey result submitted successfully.')
        return redirect(url_for('submit_results'))
    return render_template('submit-results.html', form=form)


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
    ward = fields.SelectField('Ward', validators=[validators.required()],
               choices=[choice('')]+WARDS, default='')
    email = EmailField(validators=[validators.required(),
                                   validators.Email()])
    telephone = fields.StringField(validators=[validators.required()])
    availability = fields.TextAreaField(validators=[validators.required()])
    building_type = fields.SelectField('Building type',
                        choices=[choice('')]+BUILDING_TYPES, default='',
                        validators=[validators.required()])
    num_main_rooms = fields.IntegerField('Number of main rooms ' \
                                         +'(reception + living + bedroom)')
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
            +'<a href="/pre-survey-guide/#preparation" target="_blank">'
            +'necessary preparations</a> for the survey and am happy ' \
            +'to <a href="/pre-survey-guide/#follow-ups" target="_blank"> ' \
            +'report my progress after one month and one year</a>.',
            validators=[validators.required()])


@app.route('/apply-for-a-survey', methods=['GET', 'POST'])
def apply_for_a_survey():
    form = ApplySurveyForm(request.form)
    if request.method=='POST' and helpers.validate_form_on_submit(form):
        # Add to db.
        survey = Surveys(
            name=form.name.data,
            address_line=form.address_line.data,
            postcode=form.postcode.data,
            ward=form.ward.data,
            email=form.email.data,
            telephone=form.telephone.data,
            availability=form.availability.data,
            building_type=form.building_type.data,
            num_main_rooms=form.num_main_rooms.data,
            expected_benefit=form.expected_benefit.data,
            referral=form.referral.data,
            free_survey_consideration=form.free_survey_consideration.data, )
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
@app.route('/<path:path>/')
def page(path):
    page = pages.get_or_404(path)
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
    test_user = People(email="test",
                       password=generate_password_hash("test"),
                       group='Surveyor')
    survey_1 = Surveys(name="Joe Blogs", address_line="Some street",
                       postcode="BS5 XXX")
    #item_1 = Inventory(name="Blower door", asset_number=100)
    #loan_1 = Loans(name="Jamie Hanlon", inventory=item_1)
    db.session.add(admin_user)
    db.session.add(test_user)
    db.session.add(survey_1)
    #db.session.add(item_1)
    #db.session.add(loan_1)
    db.session.commit()


#===-----------------------------------------------------------------------===#
# On the command line.
#===-----------------------------------------------------------------------===#


manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Server(host='0.0.0.0',
                                        passthrough_errors=False))

if __name__ == '__main__':
    manager.run()
