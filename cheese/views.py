import os
import random
import string
from cheese.init_app import app, db, images, pages
from cheese.definitions import *
from cheese.models import Surveys, Results, MonthFeedback, YearFeedback, \
                          ThermalImage
from flask import url_for, redirect, render_template, \
                  render_template_string, request, flash
import flask_admin as admin
from flask_admin import BaseView, helpers, expose
from flask_admin.contrib import sqla
from flask_mail import Message
from flask_user import login_required, roles_required, current_user
from flask_uploads import UploadNotAllowed
from flask_wtf import Form, FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from sqlalchemy.event import listens_for
from sqlalchemy.inspection import inspect
from wtforms import form, fields, validators
from wtforms.fields.html5 import EmailField
from wtforms_sqlalchemy.orm import model_form
from werkzeug.utils import secure_filename

#===-----------------------------------------------------------------------===#
# Admin views.
#===-----------------------------------------------------------------------===#

def choice(string):
    return (string, string)

def string_html_formatter(text):
    return Markup(''.join(['<p>'+x+'</p>' for x in text.split('\n')])) if text else ''

def view_string_html_formatter(view, context, model, name):
    return string_html_formatter(getattr(model, name))


class AdminModelView(sqla.ModelView):
    page_size = 100
    can_export = True
    can_view_details = True
    def is_accessible(self):
        return current_user.is_authenticated \
                and current_user.has_role('admin')


class ManagerModelView(AdminModelView):
    def is_accessible(self):
        return current_user.is_authenticated \
                and current_user.has_role('admin', 'manager')


class CheeseAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('user.login'))
        surveys = Surveys.query.all()
        return self.render('admin/overview.html', surveys=surveys)

    @expose('/survey/<int:survey_id>')
    def survey(self, survey_id):
        survey = Surveys.query.get(survey_id)
        return self.render('admin/survey.html',
                survey=survey,
                surveys_table=inspect(Surveys),
                results_table=inspect(Results),
                month_table=inspect(MonthFeedback),
                year_table=inspect(YearFeedback))


class UserView(AdminModelView):
    column_list = ['email', 'roles']


class SurveysView(ManagerModelView):
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
    column_formatters = {
    'expected_benefit': view_string_html_formatter,
    'availability':     view_string_html_formatter,
    'notes':            view_string_html_formatter, }
    form_args = {
        'referral':       { 'label': 'Referral from?' },
        'num_main_rooms': { 'label': 'Number of main rooms' }, }


class ResultsView(ManagerModelView):
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
    column_formatters = {
        'faults_identified': view_string_html_formatter,
        'recommendations':   view_string_html_formatter,
        'notes':             view_string_html_formatter, }
    form_widget_args = {
        'faults_identified': { 'rows': 8, 'cols': 20 },
        'recommendations':   { 'rows': 8, 'cols': 20 },
        'notes':             { 'rows': 8, 'cols': 20 }, }


class MonthFeedbackView(ManagerModelView):
    column_exclude_list = [
        'date',
        'annual_gas_kwh',
        'annual_elec_kwh',
        'annual_solid_spend',
        'renewable_contrib_kwh',
        'completed_actions',
        'planned_actions',
        'cheese_box',
        'feedback',
        'notes', ]
    column_formatters = {
        'completed_actions': view_string_html_formatter,
        'planned_actions':   view_string_html_formatter,
        'cheese_box':        view_string_html_formatter,
        'feedback':          view_string_html_formatter,
        'notes':             view_string_html_formatter, }


class YearFeedbackView(ManagerModelView):
    column_exclude_list = [
        'date',
        'annual_gas_kwh',
        'annual_elec_kwh',
        'annual_solid_spend',
        'renewable_contrib_kwh',
        'diy_work',
        'prof_work',
        'contractors_used',
        'total_spent',
        'planned_work',
        'wellbeing_improvement',
        'behaviour_changes',
        'feedback',
        'notes', ]
    column_formatters = {
        'diy_work':              view_string_html_formatter,
        'prof_work':             view_string_html_formatter,
        'contractors_used':      view_string_html_formatter,
        'planned_actions':       view_string_html_formatter,
        'wellbeing_improvement': view_string_html_formatter,
        'behaviour_changes':     view_string_html_formatter,
        'feedback':              view_string_html_formatter,
        'notes':                 view_string_html_formatter, }


class InventoryView(ManagerModelView):
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


class KitsView(ManagerModelView):
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


class ThermalImageView(ManagerModelView):
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


#===-----------------------------------------------------------------------===#
# Restricted pages.
#===-----------------------------------------------------------------------===#

@app.route('/submit-results', methods=['GET', 'POST'])
@login_required
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
        }, exclude=['date'])
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


# Unfortunately, model_form can't be used here because we need a FlaskForm for
# it to be validated properly with a FileField.
class UploadThermalImageForm(FlaskForm):
    image = FileField('Image file',
              validators=[FileRequired(),
                          FileAllowed(images, 'Only images can be uploaded')])
    description = fields.TextAreaField('Description of the image',
                    validators=[validators.required()])
    building_type = fields.SelectField('Building type',
            choices=[choice('')]+[choice(x) for x in BUILDING_TYPES],
            default='', validators=[validators.required()])
    year_of_construction = fields.IntegerField('Year of construction',
            validators=[validators.required()])
    keywords = fields.StringField("Keywords (separated by commas ',')",
                                  validators=[validators.required()])
    submitted_by = fields.StringField('Your name',
                     validators=[validators.required()])

def random_string(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) \
                for _ in range(length))

@app.route('/upload-thermal-image', methods=['GET', 'POST'])
@login_required
def upload_thermal_image():
    form = UploadThermalImageForm()
    if request.method=='POST' and form.validate_on_submit():
        image = request.files.get('image')
        try:
            filename = random_string(10)+'_'+secure_filename(image.filename)
            filename = images.save(image, name=filename)
        except UploadNotAllowed:
            flash('The uploaded file is not allowed')
        else:
            thermal_image = ThermalImage()
            thermal_image.filename = filename
            for f in ['description',
                      'building_type',
                      'year_of_construction',
                      'keywords',
                      'submitted_by']:
                    setattr(thermal_image, f, request.form.get(f))
            db.session.add(thermal_image)
            db.session.commit()
            flash('The thermal image has been submitted successfully.')
            return redirect(url_for('upload_thermal_image'))
    return render_template('upload-thermal-image.html', form=form)


@app.route('/collected-thermal-images')
@login_required
def collected_thermal_images():
    images = ThermalImage.query.all()
    keyword = request.args.get('keyword')
    # Get all keywords.
    keywords = set()
    for image in images:
        if image.keywords:
            for k in image.keywords.split(','):
                    keywords.add(k.strip().lower())
    # Filter images by keyword.
    if keyword:
             images = [x for x in images if \
                    x.keywords and keyword in x.keywords.lower()]
    return render_template('collected-thermal-images.html',
                           keywords=keywords,
                           keyword=keyword,
                           images=images)


@app.route('/received-one-month-feedback')
@login_required
def received_one_month_feedback():
    feedback = MonthFeedback.query.all()
    return render_template('received-feedback.html', type='one-month',
                           feedback=feedback)


@app.route('/received-one-year-feedback')
@login_required
def received_one_year_feedback():
    feedback = YearFeedback.query.all()
    return render_template('received-feedback.html', type='one-year',
                           feedback=feedback)


#===-----------------------------------------------------------------------===#
# Public pages.
#===-----------------------------------------------------------------------===#

def send_email(recipient, subject, message):
    msg = Message(subject=subject,
                  body=message,
                  recipients=[recipient])
    mail.send(msg)


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
                                  validators=[validators.required(),
                                              validators.Length(max=250)])
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
        exclude=['date', 'submitted_by', 'survey', 'notes'],
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
          'completed_actions': {
              'label': 'Have you already taken action to improve the thermal efficiency of your home?',
              'description': 'If so, then what have you done?',
              'validators': [validators.required()], },
          'planned_actions': {
              'label': 'What you are planning to do to in the next few years improve the thermal efficiency of your home?',
              'description': 'This can be anything from draught proofing to installing external wall insulation.',
              'validators': [validators.required()], },
          'cheese_box': {
              'label': 'Did you find your <a href="/cheese-box">CHEESE box</a> useful?',
              'description': 'We would be interested to know what you found useful and what you didn\'t.',
              'validators': [validators.required()], },
          'feedback': {
              'label': 'Do you have any feedback?',
              'description': 'We would like to hear what you think about:'
                              +' the organisation of the survey,'
                              +' the conduct of the Energy Tracers,'
                              +' the results of the survey and suggested remedies,'
                              +' the overall value for money of the survey,'
                              +' your overall satisfaction,'
                              +' and anything else at all you would like to let us know.',
              'validators': [validators.required()], },
          }
        )
    follow_up = MonthFeedback()
    form = MonthFeedbackForm(request.form, follow_up)
    if request.method=='POST' and helpers.validate_form_on_submit(form):
        form.populate_obj(follow_up)
        follow_up.submitted_by = 'Submitted from the website'
        db.session.add(follow_up)
        db.session.commit()
        # Send admin email.
        subject = 'New one month response'
        message = 'From '+form.householders_name.data+', '+form.address.data \
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
        exclude=['date', 'submitted_by', 'survey', 'notes'],
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
              'validators': [validators.InputRequired()], },
          'annual_elec_kwh': {
              'label': 'Total annual electricity usage in kWh',
              'description': kwh_help,
              'validators': [validators.InputRequired()], },
           'annual_solid_spend': {
              'label': 'Total annual spend in pounds (&pound;) on solid fuels',
              'description': 'Such as wood, coal etc.',
              'validators': [validators.InputRequired()], },
          'renewable_contrib_kwh': {
              'label': 'Total annual contribution of any renewable generation in kWh',
              'description': 'Such as from solar PV or a ground-source heat pump.',
              'validators': [validators.InputRequired()], },
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
        follow_up.submitted_by = 'Submitted from the website'
        db.session.add(follow_up)
        db.session.commit()
        # Send admin email.
        subject = 'New one year response'
        message = 'From '+form.householders_name.data+', '+form.address.data \
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
