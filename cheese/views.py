import csv
import datetime
import os
import random
import string
from cheese.models import db, WARDS, BUILDING_TYPES, Surveys, Results, \
                          MonthFeedback, YearFeedback, \
                          ThermalImage, Inventory, Kits, \
                          User, Member, UserInvitation, Role
from cheese.settings import NUM_PHASES, IMAGE_UPLOAD_FORMATS
from cheese.s3 import S3
from flask import Blueprint, current_app, url_for, redirect, render_template, \
                  render_template_string, request, flash, Markup, \
                  send_from_directory
import flask_admin
from flask_admin import helpers, expose
from flask_admin.menu import MenuLink
from flask_admin.contrib import sqla
from flask_user import login_required, current_user
from flask_flatpages import FlatPages
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from sqlalchemy.event import listens_for
from sqlalchemy.inspection import inspect
from wtforms import fields, validators, widgets
from wtforms.fields.html5 import EmailField
from wtforms_sqlalchemy.orm import model_form
from werkzeug.utils import secure_filename

mail = Mail()
pages = FlatPages()
s3 = S3()

bp = Blueprint('cheese', __name__)


class DatePickerWidget(widgets.TextInput):
    """ A custom date picker widget, using Bootstrap-datetimepicker. """
    def __call__(self, field, **kwargs):
        html = """<div class='input-group date' id='datetimepicker'>
                    <input type='text' class='form-control' %s/>
                      <span class='input-group-addon'>
                        <span class='glyphicon glyphicon-calendar'></span>
                      </span>
                   </div>"""
        return Markup(html % (self.html_params(name=field.name, **kwargs)))


class OneToFiveWidget(widgets.Input):
    """ A custom widget for 1-to-5 ratings. """
    def __call__(self, field, **kwargs):
        html = """<div class="rating-1to5">
                  <span><input type="radio" name="{0}" value="1" {1}>1</span>
                  <span><input type="radio" name="{0}" value="2" {1}>2</span>
                  <span><input type="radio" name="{0}" value="3" {1}>3</span>
                  <span><input type="radio" name="{0}" value="4" {1}>4</span>
                  <span><input type="radio" name="{0}" value="5" {1}>5</span>
                  </div>"""
        return Markup(html.format(field.name, self.html_params(**kwargs)))

def init_admin(admin):
    for phase in reversed(range(1, NUM_PHASES+1)):
        admin.add_menu_item(MenuLink(name='Phase {}'.format(phase), \
                                     url='/admin?phase={}'.format(phase)))
    admin.add_view(UserView(User, db.session,
                            name='Users',
                            category='Tables'))
    admin.add_view(MemberView(Member, db.session,
                              name='Members',
                              category='Tables'))
    admin.add_view(AdminModelView(UserInvitation, db.session,
                                  name='Invitations',
                                  category='Tables'))
    admin.add_view(AdminModelView(Role, db.session,
                                  name='Roles',
                                  category='Tables'))
    admin.add_view(SurveysView(Surveys, db.session,
                               category='Tables'))
    admin.add_view(ResultsView(Results, db.session,
                               category='Tables'))
    admin.add_view(MonthFeedbackView(MonthFeedback, db.session,
                                     name='1 month feedback',
                                     category='Tables'))
    admin.add_view(YearFeedbackView(YearFeedback, db.session,
                                    name='1 year feedback',
                                    category='Tables'))
    admin.add_view(InventoryView(Inventory, db.session,
                                 category='Tables'))
    admin.add_view(KitsView(Kits, db.session,
                            category='Tables'))
    admin.add_view(ThermalImageView(ThermalImage, db.session,
                                    name='Thermal images',
                                    category='Tables'))

#===-----------------------------------------------------------------------===#
# Signal handlers.
#===-----------------------------------------------------------------------===#

def user_registered_hook(sender, user, **extra):
    sender.logger.info("User {} registered".format(user.email))
    subject='[CHEESE] User {} registered'.format(user.email)
    message='Update their roles: '+current_app.config['URL_BASE']+'/admin/user/'
    mail.send(Message(subject=subject,
                      body=message,
                      recipients=current_app.config['ADMINS']))

def user_confirmed_email_hook(sender, user, **extra):
    sender.logger.info('User {} confirmed email'.format(user.email))

def user_changed_password_hook(sender, user, **extra):
    sender.logger.info('User {} changed password'.format(user.email))

def user_changed_username_hook(sender, user, **extra):
    sender.logger.info('User {} changed username'.format(user.email))

def user_forgot_password_hook(sender, user, **extra):
    sender.logger.info('User {} forgot password'.format(user.email))

def user_reset_password_hook(sender, user, **extra):
    sender.logger.info('User {} reset password'.format(user.email))

def user_logged_in_hook(sender, user, **extra):
    sender.logger.info('User {} logged in'.format(user.email))

def user_logged_out_hook(sender, user, **extra):
    sender.logger.info('User {} logged out'.format(user.email))

#===-----------------------------------------------------------------------===#
# Admin views.
#===-----------------------------------------------------------------------===#

def choice(string):
    return (string, string)

def string_html_formatter(text):
    return Markup(''.join(['<p>'+x+'</p>' for x in text.split('\n')])) if text else ''

def view_string_html_formatter(view, context, model, name):
    return string_html_formatter(getattr(model, name))


def has_edit_permission():
    if not current_user.is_authenticated:
        return False
    return current_user.has_role('admin', 'manager')


def validate_date(form, field):
    """
    Check whether date format is supported by strftime(), avoiding:
      ValueError: year=X is before 1900; the datetime strftime() methods require year >= 1900
    See FlaskAdmin issue: https://github.com/flask-admin/flask-admin/issues/987
    """
    if field.data:
        try:
            field.data.strftime('%d.%m.%Y')
        except ValueError:
            field.errors.append('Year must be >= 1900')
            return False
    return True


class AdminModelView(sqla.ModelView):
    """
    Admins have access to special views such as invitations, users and roles.
    """
    page_size = 100
    can_export = True
    can_view_details = True
    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        return current_user.has_role('admin')


class ManagerModelView(sqla.ModelView):
    """
    Managers have access to views such as members.
    """
    page_size = 100
    can_export = True
    can_view_details = True
    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        return current_user.has_role('admin', 'manager')


class GeneralModelView(sqla.ModelView):
    """
    All authenticated users can view the database, but not make changes.
    """
    page_size = 100
    can_export = True
    can_view_details = True
    def is_accessible(self):
        return current_user.is_authenticated
    @property
    def can_edit(self):
        return has_edit_permission()
    @property
    def can_create(self):
        return has_edit_permission()
    @property
    def can_delete(self):
        return has_edit_permission()


def get_survey_phase(date):
    phase = 1
    print date
    for start, end in zip(current_app.config['PHASE_START_DATES'][:-1], \
                          current_app.config['PHASE_START_DATES'][1:]):
        if date >= start and date < end:
            return phase
        phase += 1
    return phase


class CheeseAdminIndexView(flask_admin.AdminIndexView):
    filters = ['successful_lead',
               'possible_lead',
               'dead_lead',
               'free_survey',
               'paid_survey',
               'fee_paid',
               'fee_not_paid',
               'box_collected',
               'box_not_collected',
               'has_result',
               'no_result',
               'has_one_month',
               'no_one_month',
               'has_one_year',
               'no_one_year']

    def filter_query(self, active_phase, active_filters):
        query = Surveys.query;
        if active_phase:
            query = query.filter(Surveys.phase==active_phase)
        for name in active_filters:
            if name == 'successful_lead':
                query = query.filter(Surveys.lead_status == 'Successful')
            if name == 'possible_lead':
                query = query.filter((Surveys.lead_status == 'Possible') &
                                     (Surveys.result == None))
            if name == 'dead_lead':
                query = query.filter((Surveys.lead_status == 'Dead') &
                                     (Surveys.result == None))
            if name == 'free_survey':
                query = query.filter(Surveys.free_survey_consideration == True)
            if name == 'paid_survey':
                query = query.filter(Surveys.free_survey_consideration == False)
            if name == 'fee_paid':
                query = query.filter(Surveys.fee_paid == True)
            if name == 'fee_not_paid':
                query = query.filter((Surveys.fee_paid == False) |
                                     (Surveys.fee_paid == None))
            if name == 'box_collected':
                query = query.filter(Surveys.box_collected == True)
            if name == 'box_not_collected':
                query = query.filter((Surveys.box_collected == False) |
                                     (Surveys.box_collected == None))
            if name == 'has_result':
                query = query.filter(Surveys.result != None)
            if name == 'no_result':
                query = query.filter(Surveys.result == None)
            if name == 'has_one_month':
                query = query.filter(Surveys.month_feedback != None)
            if name == 'no_one_month':
                query = query.filter(Surveys.month_feedback == None)
            if name == 'has_one_year':
                query = query.filter(Surveys.year_feedback != None)
            if name == 'no_one_year':
                query = query.filter(Surveys.year_feedback == None)
        return query

    def sort_by_column(self, surveys, sort, reverse):
        earliest_date = current_app.config['PHASE_START_DATES'][0]
        def sort_surveys(key):
            return sorted(surveys, reverse=reverse, key=key)
        def sort_by_planned_survey_date():
            return sort_surveys(lambda x:
                     x.survey_date.date() if x.survey_date \
                                          else earliest_date)
        if sort == 'survey':
            return sort_surveys(lambda x: x.name.lower())
        elif sort == 'ward':
            return sort_surveys(lambda x: x.ward.lower())
        elif sort == 'request_date':
            return sort_surveys(lambda x:
             x.survey_request_date if x.survey_request_date \
                       else earliest_date)
        elif sort == 'survey_date':
            return sort_by_planned_survey_date()
        elif sort == 'fee_paid':
            return sort_surveys(lambda x: 2 if x.free_survey_consideration else x.fee_paid)
        elif sort == 'box_number':
            return sort_surveys(lambda x:
                     x.result[0].cheese_box_number if x.result else None)
        elif sort == 'box_collected':
            return sort_surveys(lambda x: x.box_collected)
        elif sort == 'lead_surveyor':
            return sort_surveys(lambda x:
                     x.result[0].lead_surveyor if x.result else None)
        elif sort == 'got_result':
            return sort_surveys(lambda x: x.result)
        elif sort == 'got_month':
            return sort_by_planned_survey_date()
        elif sort == 'got_year':
            return sort_by_planned_survey_date()
        else:
            return surveys

    def get_surveys(self):
        # Handle filters.
        active_phase = request.args.get('phase')
        active_filters = request.args.getlist('filter')
        surveys = self.filter_query(active_phase, active_filters).all()
        # Handle sorting by column.
        sort = request.args.get('sort')
        reverse = False if request.args.get('reverse') == '1' else True
        surveys = self.sort_by_column(surveys, sort, reverse)
        return active_phase, active_filters, reverse, surveys

    def get_delete_form(self):
        class DeleteForm(FlaskForm):
            id = fields.HiddenField(validators=[validators.required()])
            url = fields.HiddenField()
        return DeleteForm()

    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('user.login'))
        # Handle actions.
        if 'set_box_collected' in request.args:
            survey = Surveys.query.get(int(request.args.get('survey_id')))
            survey.box_collected = request.args.get('set_box_collected') == 'True'
            db.session.commit()
            args = request.args.copy()
            args.pop('set_box_collected')
            args.pop('survey_id')
            return redirect(url_for('admin.index', **args))
        if 'set_fee_paid' in request.args:
            survey = Surveys.query.get(int(request.args.get('survey_id')))
            survey.fee_paid = request.args.get('set_fee_paid') == 'True'
            db.session.commit()
            args = request.args.copy()
            args.pop('set_fee_paid')
            args.pop('survey_id')
            return redirect(url_for('admin.index', **args))
        # Render page.
        num_phases = len(current_app.config['PHASE_START_DATES'])
        phases = [str(x+1) for x in range(num_phases)]
        active_phase, active_filters, reverse, surveys = self.get_surveys()
        active_phase_start_date = None
        active_phase_end_date = None
        if active_phase:
            active_phase_start_date = current_app.config['PHASE_START_DATES'][int(active_phase)-1]
            active_phase_end_date = active_phase_start_date + datetime.timedelta(365.25)
        export_filename = 'cheese-surveys-'+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+'.csv'
        return self.render('admin/overview.html',
                           surveys=surveys,
                           reverse=(1 if reverse else 0),
                           phases=phases,
                           active_phase=active_phase,
                           active_phase_start_date=active_phase_start_date,
                           active_phase_end_date=active_phase_end_date,
                           phase_start_dates=current_app.config['PHASE_START_DATES'],
                           filters=self.filters,
                           active_filters=active_filters,
                           export_filename=export_filename,
                           edit_permission=has_edit_permission())

    @expose('/export/<filename>')
    def export(self, filename):
        export_headers = ['name',
                          'address_line',
                          'postcode',
                          'ward',
                          'email',
                          'telephone',
                          'mobile',
                          'survey_date', ]
        _, _, _, surveys = self.get_surveys()
        path = current_app.config['EXPORT_PATH']+'/'+filename
        f = open(path, 'w')
        writer = csv.writer(f)
        writer.writerow([field for field in export_headers])
        for survey in surveys:
            row = [survey.name,
                   survey.address_line,
                   survey.postcode,
                   survey.ward,
                   survey.email,
                   survey.mobile,
                   survey.survey_date, ]
            writer.writerow([unicode(s).encode("utf-8") for s in row])
        f.close()
        return send_from_directory(current_app.config['EXPORT_DIR'],
                                   filename, as_attachment=True)

    @expose('/survey/<int:survey_id>')
    def survey(self, survey_id):
        survey = Surveys.query.get(survey_id)
        return self.render('admin/survey.html',
                delete_form=self.get_delete_form(),
                survey=survey,
                surveys_table=inspect(Surveys),
                results_table=inspect(Results),
                month_table=inspect(MonthFeedback),
                year_table=inspect(YearFeedback),
                edit_permission=has_edit_permission())


class UserView(AdminModelView):
    column_list = ['email', 'roles']


class MemberView(ManagerModelView):
    column_list = ['name',
                   'registration_date']


class SurveysView(GeneralModelView):
    all_cols = set([
        'name',
        'address_line',
        'postcode',
        'ward',
        'email',
        'telephone',
        'mobile',
        'reference',
        'lead_status',
        'survey_request_date',
        'building_type',
        'num_main_rooms',
        'can_heat_comfortably',
        'expected_benefit',
        'signed_up_via',
        'referral',
        'availability',
        'free_survey_consideration',
        'fee',
        'fee_paid',
        'fee_paid_date',
        'survey_date',
        'survey_complete',
        'followed_up',
        'box_collected',
        'notes', ])
    columns_list = [
        'name',
        'ward',
        'reference',
        'survey_request_date', ]
    column_filters = columns_list
    column_exclude_list = list(all_cols - set(columns_list))
    column_formatters = {
    'expected_benefit': view_string_html_formatter,
    'availability':     view_string_html_formatter,
    'notes':            view_string_html_formatter, }
    form_args = {
        'referral':             { 'label': 'Referral from?' },
        'num_main_rooms':       { 'label': 'Number of main rooms' },
        'survey_request_date':  { 'validators': [validate_date], },
        'fee_paid_date':        { 'validators': [validate_date], },
        'survey_date':          { 'validators': [validate_date], }, }


class ResultsView(GeneralModelView):
    all_cols = [
        'date',
        'lead_surveyor',
        'assistant_surveyor',
        'householders_name',
        'address_line',
        'survey_date',
        'external_temperature',
        'loaned_cheese_box',
        'cheese_box_number',
        'building_type',
        'year_of_construction',
        'wall_construction_type',
        'primary_heating_type',
        'secondary_heating_type',
        'water_heating_type',
        'cooking_type',
        'occupation_type',
        'depth_loft_insulation',
        'number_open_fireplaces',
        'double_glazing',
        'num_occupants',
        'annual_gas_kwh',
        'annual_gas_estimated',
        'annual_gas_start_date',
        'annual_gas_end_date',
        'annual_elec_kwh',
        'annual_elec_estimated',
        'annual_elec_start_date',
        'annual_elec_end_date',
        'annual_solid_spend',
        'renewable_contribution_kwh',
        'faults_identified',
        'recommendations',
        'notes',
        'survey', ]
    columns_list = [
        'lead_surveyor',
        'assistant_surveyor',
        'householders_name',
        'address_line',
        'survey_date',
        'survey', ]
    column_filters = all_cols
    column_exclude_list = list(set(all_cols) - set(columns_list))
    column_formatters = {
        'faults_identified': view_string_html_formatter,
        'recommendations':   view_string_html_formatter,
        'notes':             view_string_html_formatter, }
    form_widget_args = {
        'faults_identified': { 'rows': 8, 'cols': 20 },
        'recommendations':   { 'rows': 8, 'cols': 20 },
        'notes':             { 'rows': 8, 'cols': 20 }, }
    form_args = {
        'survey_date':            { 'validators': [validate_date], },
        'annual_gas_start_date':  { 'validators': [validate_date], },
        'annual_gas_end_date':    { 'validators': [validate_date], },
        'annual_elec_start_date': { 'validators': [validate_date], },
        'annual_elec_end_date':   { 'validators': [validate_date], }, }

class MonthFeedbackView(GeneralModelView):
    all_cols = [
        'date',
        'submitted_by',
        'householders_name',
        'address',
        'annual_gas_kwh',
        'annual_gas_estimated',
        'annual_gas_start_date',
        'annual_gas_end_date',
        'annual_elec_kwh',
        'annual_elec_estimated',
        'annual_elec_start_date',
        'annual_elec_end_date',
        'annual_solid_spend',
        'renewable_contrib_kwh',
        'completed_actions',
        'planned_actions',
        'cheese_box',
        'satisfaction_1to5',
        'cheese_box_1to5',
        'survey_video_1to5',
        'surveyor_conduct_1to5',
        'survey_value_1to5',
        'recommend_1to5',
        'feedback',
        'notes',
        'survey', ]
    columns_list = [
        'date',
        'submitted_by',
        'householders_name',
        'address',
        'survey', ]
    column_filters = all_cols
    column_exclude_list = list(set(all_cols) - set(columns_list))
    column_formatters = {
        'completed_actions': view_string_html_formatter,
        'planned_actions':   view_string_html_formatter,
        'cheese_box':        view_string_html_formatter,
        'feedback':          view_string_html_formatter,
        'notes':             view_string_html_formatter, }
    form_args = {
        'annual_gas_start_date':  { 'validators': [validate_date], },
        'annual_gas_end_date':    { 'validators': [validate_date], },
        'annual_elec_start_date': { 'validators': [validate_date], },
        'annual_elec_end_date':   { 'validators': [validate_date], }, }


class YearFeedbackView(GeneralModelView):
    all_cols = [
        'date',
        'submitted_by',
        'householders_name',
        'address',
        'annual_gas_kwh',
        'annual_gas_estimated',
        'annual_gas_start_date',
        'annual_gas_end_date',
        'annual_elec_kwh',
        'annual_elec_estimated',
        'annual_elec_start_date',
        'annual_elec_end_date',
        'annual_solid_spend',
        'renewable_contrib_kwh',
        'diy_work',
        'prof_work',
        'contractors_used',
        'total_spent',
        'total_spent_diy',
        'total_spent_local',
        'planned_work',
        'wellbeing_improvement',
        'behaviour_changes',
        'feedback',
        'notes',
        'survey', ]
    columns_list = [
        'date',
        'submitted_by',
        'householders_name',
        'address',
        'survey', ]
    column_filters = all_cols
    column_exclude_list = list(set(all_cols) - set(columns_list))
    column_formatters = {
        'diy_work':              view_string_html_formatter,
        'prof_work':             view_string_html_formatter,
        'contractors_used':      view_string_html_formatter,
        'planned_actions':       view_string_html_formatter,
        'wellbeing_improvement': view_string_html_formatter,
        'behaviour_changes':     view_string_html_formatter,
        'feedback':              view_string_html_formatter,
        'notes':                 view_string_html_formatter, }
    form_args = {
        'annual_gas_start_date':  { 'validators': [validate_date], },
        'annual_gas_end_date':    { 'validators': [validate_date], },
        'annual_elec_start_date': { 'validators': [validate_date], },
        'annual_elec_end_date':   { 'validators': [validate_date], }, }


class InventoryView(GeneralModelView):
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
    form_args = {
        'date_of_purchase': { 'validators': [validate_date], },
        'credit_date':      { 'validators': [validate_date], }, }


class KitsView(GeneralModelView):
    form_columns = ['name', 'notes', 'inventory']
    column_list = form_columns
    column_filters = column_list


@listens_for(ThermalImage, 'after_delete')
def del_thermal_image(mapper, connection, target):
    if target.filename:
        try:
            filename = os.path.join(current_app.config['UPLOADED_IMAGES_DEST'],
                                    target.filename)
            os.remove(filename)
        except OSError:
            pass


class ThermalImageView(GeneralModelView):
    can_create = False
    def _list_thumbnail(view, context, model, name):
        if not model.filename:
            return ''
        filename = os.path.join(current_app.config['UPLOADED_IMAGES_URL'],
                                model.filename)
        thumb_filename = thumb.thumbnail(filename, '100x100')
        return Markup('<a href="/{}"><img src="{}"></a>'.format(filename,
                                                                thumb_filename))
    column_formatters = { 'filename': _list_thumbnail, }
    column_exclude_list = ['date', ]


#===-----------------------------------------------------------------------===#
# Restricted pages.
#===-----------------------------------------------------------------------===#

@bp.route('/submit-results', methods=['GET', 'POST'])
@login_required
def submit_results():
    ResultsForm = model_form(Results, db_session=db.session, field_args={
        "survey":                     { "label": "Survey (type to search)", },
        "lead_surveyor":              { "label": "Lead surveyor", },
        "assistant_surveyor":         { "label": "Assistant surveyor", },
        "householders_name":          { "label": "Householder's name", },
        "address_line":               { "label": "Address line", },
        "survey_date":                { "label": "Survey date (dd/mm/yyyy)",
                                        "format": "%d/%m/%Y",
                                        "widget": DatePickerWidget(),
                                        "validators": [validate_date], },
        "external_temperature":       { "label": "External temperature (C)", },
        "loaned_cheese_box":          { "label": "CHEESE box loaned?", },
        "cheese_box_number":          { "label": "CHEESE box number", },
        "building_type" :             { "label": "Building type", },
        "year_of_construction":       { "label": "Year of construction", },
        "wall_construction":          { "label": "Wall construction", },
        "occupation_type":            { "label": "Occupation type", },
        "primary_heating_type":       { "label": "Primary heating type", },
        "secondary_heating_type":     { "label": "Secondary heating type", },
        "water_heating_type":         { "label": "Primary water heating type", },
        "cooking_type":               { "label": "Primary cooking type", },
        "depth_loft_insulation":      { "label": "Depth of loft insulation (mm)", },
        "number_open_fireplaces":     { "label": "Number of open fireplaces", },
        "double_glazing":             { "label": "Amount of double glazing (%)", },
        "num_occupants":              { "label": "Number of occupants", },
        "annual_gas_kwh":             { "label": "Annual consumption (kWh)", },
        "annual_gas_estimated":       { "label": "Is the value based on estimated use?", },
        "annual_gas_start_date":      { "label": "Start date (dd/mm/yyy)",
                                        "format": "%d/%m/%Y",
                                        "widget": DatePickerWidget(),
                                        "validators": [validators.Optional(),
                                                       validate_date], },
        "annual_gas_end_date":        { "label": "End date (dd/mm/yyy)",
                                        "format": "%d/%m/%Y",
                                        "widget": DatePickerWidget(),
                                        "validators": [validators.Optional(),
                                                       validate_date], },
        "annual_elec_kwh":            { "label": "Annual consumption (kWh)", },
        "annual_elec_estimated":      { "label": "Is the value based on estimated use??", },
        "annual_elec_start_date":     { "label": "Start date (dd/mm/yyy)",
                                        "format": "%d/%m/%Y",
                                        "widget": DatePickerWidget(),
                                        "validators": [validators.Optional(),
                                                       validate_date], },
        "annual_elec_end_date":       { "label": "End date (dd/mm/yyy)",
                                        "format": "%d/%m/%Y",
                                        "widget": DatePickerWidget(),
                                        "validators": [validators.Optional(),
                                                       validate_date], },
        "annual_solid_spend":         { "label": "Annual spend on solid fuels (&pound;)", },
        "renewable_contribution_kwh": { "label": "Annual contribution from renewable generation (kWh)", },
        "faults_identified":          { "label": "Faults identified", },
        }, exclude=['date'])
    results = Results()
    form = ResultsForm(request.form, results)
    if request.method=='POST' and helpers.validate_form_on_submit(form):
        form.populate_obj(results)
        db.session.add(results)
        db.session.commit()
        # Send watchers email.
        subject = '[CHEESE] New survey result'
        message = 'For '+results.householders_name+', '+results.address_line \
                  + ' at '+str(datetime.datetime.today())+': ' \
                  + current_app.config['URL_BASE']+str(url_for('results.details_view', id=results.id))
        mail.send(Message(subject=subject,
                          body=message,
                          recipients=current_app.config['WATCHERS']))
        # Flash success message.
        flash('Survey result submitted successfully.')
        return redirect(url_for('cheese.submit_results'))
    return render_template('submit-results.html', form=form)


# Unfortunately, model_form can't be used here because we need a FlaskForm for
# it to be validated properly with a FileField.
class UploadThermalImageForm(FlaskForm):
    image = FileField('Image file',
              validators=[FileRequired(),
                          FileAllowed(IMAGE_UPLOAD_FORMATS,
                                      'Only images can be uploaded')])
    description = fields.TextAreaField('Description of the image',
                    validators=[validators.required()])
    building_type = fields.SelectField('Building type',
            choices=[choice('')]+[choice(x) for x in BUILDING_TYPES],
            default='', validators=[validators.required()])
    year_of_construction = fields.IntegerField('Year of construction',
            validators=[validators.required()])
    keywords = fields.StringField("Keywords (separated by commas ',')",
                                  validators=[validators.required()])

def random_string(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) \
                for _ in range(length))

@bp.route('/upload-thermal-image', methods=['GET', 'POST'])
@login_required
def upload_thermal_image():
    form = UploadThermalImageForm()
    if request.method=='POST' and form.validate_on_submit():
        image = request.files.get('image')
        filename = random_string(10)+'_'+secure_filename(image.filename)
        s3.upload_fileobj_thermal_image(image, filename)
        thermal_image = ThermalImage()
        thermal_image.filename = filename
        for f in ['description',
                  'building_type',
                  'year_of_construction',
                  'keywords', ]:
                setattr(thermal_image, f, request.form.get(f))
        setattr(thermal_image, 'user', User.query.get(current_user.get_id()))
        db.session.add(thermal_image)
        db.session.commit()
        # Send watchers email.
        subject = '[CHEESE] New themrmal image'
        message = 'From '+str(thermal_image.user) \
                  + ' at '+str(datetime.datetime.today())+': ' \
                  + current_app.config['URL_BASE']+str(url_for('thermalimage.details_view', id=thermal_image.id))
        mail.send(Message(subject=subject,
                          body=message,
                          recipients=current_app.config['WATCHERS']))
        # Flash success message.
        flash('The thermal image has been submitted successfully.')
        return redirect(url_for('cheese.upload_thermal_image'))
    return render_template('upload-thermal-image.html', form=form)


@bp.route('/collected-thermal-images')
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


#===-----------------------------------------------------------------------===#
# Public pages.
#===-----------------------------------------------------------------------===#

class ApplySurveyForm(FlaskForm):
    name = fields.StringField(validators=[validators.required(),
                                          validators.Length(max=100)])
    address_line = fields.StringField(validators=[validators.required(),
                                                  validators.Length(max=100)])
    postcode = fields.StringField(validators=[validators.required(),
                                              validators.Length(max=10)])
    ward = fields.SelectField('Ward',
               choices=[choice('')]+[choice(x) for x in WARDS],
               default='', validators=[validators.required(),
                                       validators.Length(max=50)])
    email = EmailField(validators=[validators.required(),
                                   validators.Email(),
                                   validators.Length(max=100)])
    telephone = fields.StringField(validators=[validators.required(),
                                               validators.Length(max=20)])
    mobile = fields.StringField(validators=[validators.required(),
                                            validators.Length(max=20)])
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
        fields.BooleanField('I <strong>agree</strong> to make the  ' \
            +'<a href="/pre-survey-guide#preparation" target="_blank">'
            +'necessary preparations</a> for the survey and am happy ' \
            +'to <a href="/pre-survey-guide#follow-ups" target="_blank"> ' \
            +'report my progress after one month and one year</a>.',
            validators=[validators.required()])
    photo_release = \
        fields.BooleanField('I <strong>agree</strong> to any of the ' \
            +'still photos to be taken during my survey that do not ' \
            +'clearly identify a specific person or place to be used in a ' \
            +'publicly-accessible record on thermal faults and energy ' \
            +'efficiency.')


@bp.route('/apply-for-a-survey', methods=['GET', 'POST'])
def apply_for_a_survey():
    form = ApplySurveyForm(request.form)
    today = datetime.date.today()
    notice = ''
    if (today.month > 3 and today.month < 9): # Display notice April to August
      notice = """The {}/{} surveying season has now finished, but you can still apply
      for a survey next winter, between November {} and April {}.""".format(
        today.year-1, today.year, today.year, today.year+1)
    if request.method=='POST' and helpers.validate_form_on_submit(form):
        # Add to db.
        survey = Surveys()
        form.populate_obj(survey)
        survey.signed_up_via = 'The CHEESE website'
        survey.phase = get_survey_phase(datetime.datetime.utcnow().date())
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
        mail.send(Message(subject=subject,
                          body=message,
                          recipients=[form.email.data]))
        # Send watchers email.
        subject = '[CHEESE] New request for a survey'
        message = 'From '+survey.name+', '+survey.address_line \
                  + ' at '+str(datetime.datetime.today())+': ' \
                  + current_app.config['URL_BASE']+str(url_for('surveys.details_view', id=survey.id))
        mail.send(Message(subject=subject,
                          body=message,
                          recipients=current_app.config['WATCHERS']))
        # Success page.
        page = pages.get('application-successful')
        return render_template('page.html', page=page)
    return render_template('apply-for-a-survey.html', form=form, notice=notice)


@bp.route('/one-month-feedback', methods=['GET', 'POST'])
def one_month_feedback():
    not_needed = 'We only need this if we didn\'t collect this during the survey.'
    numbers_only = 'Only use digits and (optionally) a decimal point, no other punctuation or symbols.'
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
              'label': 'Total annual gas use in kWh',
              'description': numbers_only, },
          'annual_gas_estimated': {
              'label': 'Is this figure based on estimated use (rather than meter readings)?', },
          'annual_gas_start_date': {
              'label': 'Start date (mm/dd/yyy)',
              "format": "%d/%m/%Y",
              'widget': DatePickerWidget(),
              "validators": [validators.Optional(),
                             validate_date], },
          'annual_gas_end_date': {
              'label': 'End date (mm/dd/yyy)',
              "format": "%d/%m/%Y",
              'widget': DatePickerWidget(),
              "validators": [validators.Optional(),
                             validate_date], },
          'annual_elec_kwh': {
              'label': 'Total annual electricity usage in kWh',
              'description': numbers_only, },
          'annual_elec_estimated': {
              'label': 'Is this figure based on estimated use (rather than meter readings)?', },
          'annual_elec_start_date': {
              'label': 'Start date (mm/dd/yyy)',
              "format": "%d/%m/%Y",
              'widget': DatePickerWidget(),
              "validators": [validators.Optional(),
                             validate_date], },
          'annual_elec_end_date': {
              'label': 'End date (mm/dd/yyy)',
              "format": "%d/%m/%Y",
              'widget': DatePickerWidget(),
              "validators": [validators.Optional(),
                             validate_date], },
          'annual_solid_spend': {
              'label': 'Total annual spend in pounds (&pound;) on solid fuels',
              'description': 'Such as wood, coal etc. '+not_needed, },
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
          'satisfaction_1to5': {
              'label': 'How satisified were you with the survey overall? (1: least, to 5: most)',
              'widget': OneToFiveWidget(), },
          'cheese_box_1to5': {
              'label': 'How useful did you find the CHEESE box? (1: least, to 5: most)',
              'widget': OneToFiveWidget(), },
          'survey_video_1to5': {
              'label': 'How useful have you find the survey video? (1: not at all, to 5: very)',
              'widget': OneToFiveWidget(), },
          'surveyor_conduct_1to5': {
              'label': 'How was the conduct of the surveyor? (1: poor, to 5: excellent)',
              'widget': OneToFiveWidget(), },
          'survey_value_1to5': {
              'label': 'Was the survey good value for money? (1: disagree, to 5: agree)',
              'widget': OneToFiveWidget(), },
          'recommend_1to5': {
              'label': 'Are you likely to recommend the survey to a friend or neighbour? (1: unlikely, to 5: definitely)',
              'widget': OneToFiveWidget(), },
          'cheese_box': {
              'label': 'Can you explain your <a href="/cheese-box">CHEESE box</a> score?',
              'description': 'We would be interested to know specifically what you found useful and what you didn\'t.',
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
        # Send watchers email.
        subject = '[CHEESE] New one-month response'
        message = 'From '+follow_up.householders_name+', '+follow_up.address \
                  + ' at '+str(datetime.datetime.today())+': ' \
                  + current_app.config['URL_BASE']+str(url_for('monthfeedback.details_view', id=follow_up.id))
        mail.send(Message(subject=subject,
                          body=message,
                          recipients=current_app.config['WATCHERS']))
        # Flash success message.
        flash('Your one month feedback was submitted successfully, thank you.')
        return redirect(url_for('cheese.one_month_feedback'))
    return render_template('one-month-feedback.html', form=form)


@bp.route('/one-year-feedback', methods=['GET', 'POST'])
def one_year_feedback():
    numbers_only = 'Only use digits and (optionally) a decimal point, no other punctuation or symbols.'
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
              'label': 'Total annual gas use in kWh',
              'description': numbers_only,
              'validators': [validators.InputRequired()], },
          'annual_gas_estimated': {
              'label': 'Is this figure based on estimated use (rather than meter readings)?', },
          'annual_gas_start_date': {
              'label': 'Start date (mm/dd/yyy)',
              "format": "%d/%m/%Y",
              'widget': DatePickerWidget(),
              'validators': [validators.InputRequired(),
                             validate_date], },
          'annual_gas_end_date': {
              'label': 'End date (mm/dd/yyy)',
              "format": "%d/%m/%Y",
              'widget': DatePickerWidget(),
              'validators': [validators.InputRequired(),
                             validate_date], },
          'annual_elec_kwh': {
              'label': 'Total annual electricity usage in kWh',
              'description': numbers_only,
              'validators': [validators.InputRequired()], },
          'annual_elec_estimated': {
              'label': 'Is this figure based on estimated use (rather than meter readings)?', },
          'annual_elec_start_date': {
              'label': 'Start date (mm/dd/yyy)',
              "format": "%d/%m/%Y",
              'widget': DatePickerWidget(),
              'validators': [validators.InputRequired(),
                             validate_date], },
          'annual_elec_end_date': {
              'label': 'End date (mm/dd/yyy)',
              "format": "%d/%m/%Y",
              'widget': DatePickerWidget(),
              'validators': [validators.InputRequired(),
                             validate_date], },
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
          'total_spent_diy': {
              'label': 'Approximately how much did you spend on DIY?', },
          'total_spent_local': {
              'label': 'Approximately how much did you spend on local contractors?', },
          'planned_work': {
              'label': 'Do you have any further work planned? And, if so, what?',
              'validators': [validators.required()], },
          'wellbeing_improvement': {
              'label': 'Have the actions you\'ve taken made your house feel warmer?',
              'description': 'Perhaps even if you haven\'t saved any money on your bills!', },
          'behaviour_temperature': {
              'label': 'Has the period and temperature you use the heating for changed, and if so, how?',
              'validators': [validators.required()], },
          'behaviour_space': {
              'label': 'Do you use space in your home differently now, and if so, how?',
              'validators': [validators.required()], },
          'behaviour_changes': {
              'label': 'How else has your behaviour changed after the survey?',
              'validators': [validators.required()], },
          'feedback':
            { 'label': 'Lastly, do you have any other feedback on the CHEESE Project?',
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
        # Send watchers email.
        subject = '[CHEESE] New one-year response'
        message = 'From '+follow_up.householders_name+', '+follow_up.address \
                  + ' at '+str(datetime.datetime.today())+': ' \
                  + current_app.config['URL_BASE']+str(url_for('yearfeedback.details_view', id=follow_up.id))
        mail.send(Message(subject=subject,
                          body=message,
                          recipients=current_app.config['WATCHERS']))
        # Flash success message.
        flash('Your one year feedback was submitted successfully, thank you.')
        return redirect(url_for('cheese.one_year_feedback'))
    return render_template('one-year-feedback.html', form=form)


@bp.route('/apply-for-membership', methods=['GET', 'POST'])
def apply_for_membership():
    MembershipForm = model_form(Member, db_session=db.session,
        exclude=['application_date', 'registration_date', 'notes'],
        field_args={
          'name': {
            'label': 'Organisation name or name of individual if individual membership*',
            'validators': [validators.required()], },
          'address': {
            'label': 'Address*',
            'validators': [validators.required()], },
          'email': {
            'label': 'Contact email address*',
            'description': 'This will act as the primary point of contact',
            'validators': [validators.required()], },
          'telephone': {
            'label': 'Contact telephone number', },
          'representative_1_name': {
            'label': 'Name', },
          'representative_1_email': {
            'label': 'Contact email address', },
          'representative_1_telephone': {
            'label': 'Contact telephone number', },
          'representative_2_name': {
            'label': 'Name', },
          'representative_2_email': {
            'label': 'Contact email address', },
          'representative_2_telephone': {
            'label': 'Contact telephone number', },
           })
    member = Member()
    form = MembershipForm(request.form, member)
    if request.method=='POST' and helpers.validate_form_on_submit(form):
        form.populate_obj(member)
        db.session.add(member)
        db.session.commit()
        # Send watchers email.
        subject = '[CHEESE] New application for member'
        message = 'From '+member.name+', '+member.address \
                  + ' at '+str(datetime.datetime.today())+': ' \
                  + current_app.config['URL_BASE']+str(url_for('member.details_view', id=member.id))
        mail.send(Message(subject=subject,
                          body=message,
                          recipients=current_app.config['WATCHERS']))
        # Flash success message.
        flash('Your membership application was submitted successfully, thank you.')
        return redirect(url_for('cheese.apply_for_membership'))
    return render_template('apply-for-membership.html', form=form)


def get_articles():
    articles = [x for x in pages if 'article' in x.meta]
    articles = sorted(articles, reverse=True,
                        key=lambda p: p.meta['date'])
    # Render any templating in each news item.
    for item in articles:
        item.html = render_template_string(item.html)
        item.date_str = item.meta['date'].strftime('%B %Y')
    return articles


@bp.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@bp.errorhandler(413)
def request_entity_too_large(error):
    return render_template('413.html'), 413

@bp.route('/robots.txt')
def rom_root():
    return send_from_directory(current_app.static_folder, request.path[1:])

# For debug deployment only. Will be overridden by Nginx rule in production.
@bp.route('/assets/<path:filename>')
def assets(filename):
    url = current_app.config['S3_PREFIX']+'/'+filename
    return redirect(url, code=302)

@bp.route('/')
def index():
    articles = get_articles()
    if len(articles) >= 3:
        articles = articles[:3]
    return render_template('index.html', articles=articles)

@bp.route('/<path:path>')
def page(path):
    page = pages.get_or_404(path)
    if 'article' in page.meta:
        return render_template('404.html'), 404
    template = page.meta.get('template', 'page.html')
    return render_template(template, page=page)

@bp.route('/news')
def news():
    return render_template('news.html', articles=get_articles())

@bp.route('/news/<path:path>')
def article(path):
    page = pages.get_or_404(path)
    if not 'article' in page.meta:
        return render_template('404.html'), 404
    return render_template('article.html', page=page,
                           path=current_app.config['URL_BASE']+request.path)

def flatpage_template():
    # Flat page with template code.
    print request.url_rule.rule
    page = pages.get(request.url_rule.rule[1:])
    page.html = render_template_string(page.html)
    template = page.meta.get('template', 'page.html')
    return render_template(template, page=page)

home_surveys           = bp.route('/home-surveys')(flatpage_template)
pre_surevey_guide      = bp.route('/pre-survey-guide')(flatpage_template)
cheese_box             = bp.route('/cheese-box')(flatpage_template)
overview               = bp.route('/overview')(flatpage_template)
partners               = bp.route('/partners')(flatpage_template)
management_and_funding = bp.route('/management-and-funding')(flatpage_template)
media_coverage         = bp.route('/media-coverage')(flatpage_template)
publicity_materials    = bp.route('/publicity-materials')(flatpage_template)
