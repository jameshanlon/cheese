import csv
import datetime
import os
import random
import string
from collections import defaultdict
from cheese.models import db, \
                          BuildingTypes, \
                          WallConstructionTypes, \
                          OccupationTypes, \
                          SpaceHeatingTypes, \
                          WaterHeatingTypes, \
                          CookingTypes, \
                          Wards, \
                          SurveyLeadStatuses, \
                          Surveys, \
                          Results, \
                          MonthFeedback, \
                          YearFeedback, \
                          ThermalImage, \
                          Inventory, \
                          Kits, \
                          User, \
                          Member, \
                          UserInvitation, \
                          Role
from cheese.forms import ApplySurveyForm, \
                         UploadThermalImageForm, \
                         OneMonthFeedbackForm, \
                         OneYearFeedbackForm, \
                         MembershipForm, \
                         create_upload_thermal_image_form, \
                         create_apply_survey_form, \
                         create_submit_results_form, \
                         validate_date
from cheese.settings import NUM_PHASES
from cheese.thumbnail import get_thumbnail
from cheese.s3 import S3
from flask import Blueprint, \
                  current_app, \
                  url_for, \
                  redirect, \
                  render_template, \
                  render_template_string, \
                  request, \
                  flash, \
                  Markup, \
                  send_from_directory
import flask_admin
from flask_admin import helpers, expose
from flask_admin.menu import MenuLink
from flask_admin.contrib import sqla
from flask_user import login_required, current_user
from flask_flatpages import FlatPages
from flask_wtf import FlaskForm
from flask_mail import Mail, Message
from sqlalchemy.event import listens_for
from sqlalchemy.inspection import inspect
from werkzeug.utils import secure_filename
from wtforms import fields, validators

mail = Mail()
pages = FlatPages()
s3 = S3()

bp = Blueprint('cheese', __name__)


def init_admin(admin):
    for phase in reversed(range(1, NUM_PHASES+1)):
        admin.add_menu_item(MenuLink(name='Phase {}'.format(phase), \
                                     url='/admin?phase={}'.format(phase)))
    # Tables.
    admin.add_view(MemberView(Member, db.session,
                              name='Members',
                              category='Records'))
    admin.add_view(SurveysView(Surveys, db.session,
                               category='Records'))
    admin.add_view(ResultsView(Results, db.session,
                               category='Records'))
    admin.add_view(MonthFeedbackView(MonthFeedback, db.session,
                                     name='1 month feedback',
                                     category='Records'))
    admin.add_view(YearFeedbackView(YearFeedback, db.session,
                                    name='1 year feedback',
                                    category='Records'))
    admin.add_view(ThermalImageView(ThermalImage, db.session,
                                    name='Thermal images',
                                    category='Records'))
    admin.add_view(InventoryView(Inventory, db.session,
                                 category='Records'))
    admin.add_view(KitsView(Kits, db.session,
                            category='Records'))
    # Admin.
    admin.add_view(UserView(User, db.session,
                            name='Users',
                            category='Admin'))
    admin.add_view(AdminModelView(UserInvitation, db.session,
                                  name='Invitations',
                                  category='Admin'))
    admin.add_view(EnumModelView(Role, db.session,
                                 name='Roles',
                                 category='Admin'))
    admin.add_view(EnumModelView(BuildingTypes, db.session,
                                 name='Building types',
                                 category='Admin'))
    admin.add_view(EnumModelView(WallConstructionTypes, db.session,
                                 name='Wall construction types',
                                 category='Admin'))
    admin.add_view(EnumModelView(OccupationTypes, db.session,
                                 name='Occupation types',
                                 category='Admin'))
    admin.add_view(EnumModelView(SpaceHeatingTypes, db.session,
                                 name='Space heating types',
                                 category='Admin'))
    admin.add_view(EnumModelView(WaterHeatingTypes, db.session,
                                 name='Water heating types',
                                 category='Admin'))
    admin.add_view(EnumModelView(CookingTypes, db.session,
                                 name='Cooking types',
                                 category='Admin'))
    admin.add_view(EnumModelView(Wards, db.session,
                                  name='Wards',
                                  category='Admin'))

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
    for start, end in zip(current_app.config['PHASE_START_DATES'][:-1], \
                          current_app.config['PHASE_START_DATES'][1:]):
        if date >= start and date < end:
            return phase
        phase += 1
    return phase

def lead_status_id(name):
    return SurveyLeadStatuses.query.filter(SurveyLeadStatuses.name==name).first().id

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
                query = query.filter(Surveys.lead_status_id == lead_status_id('Successful'))
            if name == 'possible_lead':
                query = query.filter((Surveys.lead_status_id == lead_status_id('Possible')) &
                                     (Surveys.result == None))
            if name == 'dead_lead':
                query = query.filter((Surveys.lead_status_id == lead_status_id('Dead')) &
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
            id = fields.HiddenField(validators=[validators.Required()])
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


class EnumModelView(AdminModelView):
    can_delete = False


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
        key = current_app.config['UPLOADED_IMAGES_PREFIX']+'/'+target.filename
        s3.delete_thermal_image(key)


class ThermalImageView(GeneralModelView):
    can_create = False
    def _list_thumbnail(view, context, model, name):
        if not model.filename:
            return ''
        key = current_app.config['UPLOADED_IMAGES_PREFIX']+'/'+model.filename
        url = current_app.config['UPLOADED_IMAGES_URL']+'/'+model.filename
        thumb_filename = get_thumbnail(key, '100x100')
        return Markup('<a href="/{}"><img src="{}"></a>'.format(url,
                                                                thumb_filename))
    column_formatters = { 'filename': _list_thumbnail, }
    column_exclude_list = ['date', ]


#===-----------------------------------------------------------------------===#
# Restricted pages.
#===-----------------------------------------------------------------------===#

@bp.route('/submit-results', methods=['GET', 'POST'])
@login_required
def submit_results():
    form = create_submit_results_form(db.session, request.form)
    if request.method=='POST':
        if helpers.validate_form_on_submit(form):
            results = Results()
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
        else:
            flash('There were problems with your form.', 'error')
    return render_template('submit-results.html', form=form)


def random_string(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) \
                for _ in range(length))

@bp.route('/upload-thermal-image', methods=['GET', 'POST'])
@login_required
def upload_thermal_image():
    form = create_upload_thermal_image_form(db.session)
    if request.method=='POST':
        if form.validate_on_submit():
            image = request.files.get('image_file')
            filename = random_string(10)+'_'+secure_filename(image.filename)
            s3.upload_fileobj_thermal_image(image, filename)
            thermal_image = ThermalImage()
            thermal_image.filename = unicode(filename)
            for f in ['description',
                      'year_of_construction',
                      'keywords', ]:
                    setattr(thermal_image, f, request.form.get(f))
            building_type_id = int(request.form.get('building_type'))
            building_type = BuildingTypes.query.filter(BuildingTypes.id==building_type_id).first()
            setattr(thermal_image, 'building_type', building_type)
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
        else:
            flash('There were problems with your form.', 'error')
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

@bp.route('/customer-feedback')
@login_required
def customer_feedback():
    month_feedback = MonthFeedback.query.all()
    num_phases = len(current_app.config['PHASE_START_DATES'])
    phases = reversed([x+1 for x in range(num_phases)])
    return render_template('customer-feedback.html',
                           month_feedback=month_feedback,
                           phases=phases)

@bp.route('/survey-statistics')
@login_required
def survey_stats():
    class Stats(object):
        pass
    num_phases = len(current_app.config['PHASE_START_DATES'])
    phases = [x+1 for x in reversed(range(num_phases))]
    stats = defaultdict(Stats)
    for phase in phases:
        q = Surveys.query.filter(Surveys.phase==phase)
        num_surveys   = len(q.all())
        num_dead      = len(q.filter(Surveys.lead_status_id==lead_status_id('Dead')).all())
        num_possible  = len(q.filter(Surveys.lead_status_id==lead_status_id('Possible')).all())
        num_free      = len(q.filter(Surveys.free_survey_consideration==True).all())
        num_results   = len(q.filter(Surveys.result!=None).all())
        num_one_month = len(q.filter(Surveys.month_feedback!=None).all())
        num_one_year  = len(q.filter(Surveys.year_feedback!=None).all())
        setattr(stats[phase], 'num_surveys', num_surveys)
        setattr(stats[phase], 'num_dead', num_dead)
        setattr(stats[phase], 'num_possible', num_possible)
        setattr(stats[phase], 'num_free', num_free)
        setattr(stats[phase], 'num_results', num_results)
        setattr(stats[phase], 'num_one_month', num_one_month)
        setattr(stats[phase], 'num_one_year', num_one_year)
    return render_template('survey-statistics.html',
                           phases=phases,
                           stats=stats)

#===-----------------------------------------------------------------------===#
# Public pages.
#===-----------------------------------------------------------------------===#

@bp.route('/apply-for-a-survey', methods=['GET', 'POST'])
def apply_for_a_survey():
    form = create_apply_survey_form(db.session, request.form)
    today = datetime.date.today()
    notice = ''
    if (today.month > 3 and today.month < 9): # Display notice April to August
      notice = """The {}/{} surveying season has now finished, but you can still apply
      for a survey next winter, between November {} and April {}.""".format(
        today.year-1, today.year, today.year, today.year+1)
    if request.method=='POST':
        if helpers.validate_form_on_submit(form):
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
        else:
            flash('There were problems with your form.', 'error')
    return render_template('apply-for-a-survey.html', form=form, notice=notice)



@bp.route('/one-month-feedback', methods=['GET', 'POST'])
def one_month_feedback():
    form = OneMonthFeedbackForm(request.form)
    if request.method=='POST':
        if helpers.validate_form_on_submit(form):
            month_feedback = MonthFeedback()
            form.populate_obj(month_feedback)
            month_feedback.submitted_by = 'Submitted from the website'
            db.session.add(month_feedback)
            db.session.commit()
            # Send watchers email.
            subject = '[CHEESE] New one-month response'
            message = 'From '+month_feedback.householders_name+', '+month_feedback.address \
                + ' at '+str(datetime.datetime.today())+': ' \
                + current_app.config['URL_BASE']+str(url_for('monthfeedback.details_view', id=month_feedback.id))
            mail.send(Message(subject=subject,
                              body=message,
                              recipients=current_app.config['WATCHERS']))
            # Flash success message.
            flash('Your one-month feedback was submitted successfully, thank you.')
            return redirect(url_for('cheese.one_month_feedback'))
        else:
            flash('There were problems with your form.', 'error')
    return render_template('one-month-feedback.html', form=form)


@bp.route('/one-year-feedback', methods=['GET', 'POST'])
def one_year_feedback():
    form = OneYearFeedbackForm(request.form)
    if request.method=='POST':
        if helpers.validate_form_on_submit(form):
            year_feedback = YearFeedback()
            form.populate_obj(year_feedback)
            year_feedback.submitted_by = 'Submitted from the website'
            db.session.add(year_feedback)
            db.session.commit()
            # Send watchers email.
            subject = '[CHEESE] New one-year response'
            message = 'From '+year_feedback.householders_name+', '+year_feedback.address \
                + ' at '+str(datetime.datetime.today())+': ' \
                + current_app.config['URL_BASE']+str(url_for('yearfeedback.details_view', id=year_feedback.id))
            mail.send(Message(subject=subject,
                              body=message,
                              recipients=current_app.config['WATCHERS']))
            # Flash success message.
            flash('Your one-year feedback was submitted successfully, thank you.')
            return redirect(url_for('cheese.one_year_feedback'))
        else:
            flash('There were problems with your form.', 'error')
    return render_template('one-year-feedback.html', form=form)


@bp.route('/apply-for-membership', methods=['GET', 'POST'])
def apply_for_membership():
    form = MembershipForm(request.form)
    if request.method=='POST':
        if helpers.validate_form_on_submit(form):
            member = Member()
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
        else:
            flash('There were problems with your form.', 'error')
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
def static_from_root():
    return send_from_directory(current_app.static_folder, request.path[1:])

# For debug deployment only. Will be overridden by Nginx rule in production.
@bp.route('/assets/<path:filename>')
def assets(filename):
    url = current_app.config['S3_URL_PREFIX']+'/'+filename
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

@bp.route('/energy-tracer-resources')
@login_required
def energy_tracer_resources():
    page = pages.get_or_404('energy-tracer-resources')
    page.html = render_template_string(page.html)
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
    page.html = render_template_string(page.html)
    page.date_str = page.meta['date'].strftime('%B %Y')
    return render_template('article.html', page=page,
                           path=current_app.config['URL_BASE']+request.path)

def flatpage_template():
    # Flat page with template code.
    page = pages.get(request.url_rule.rule[1:])
    page.html = render_template_string(page.html)
    template = page.meta.get('template', 'page.html')
    return render_template(template, page=page)

home_surveys           = bp.route('/home-surveys')(flatpage_template)
pre_surevey_guide      = bp.route('/pre-survey-guide')(flatpage_template)
cheese_box             = bp.route('/cheese-box')(flatpage_template)
overview               = bp.route('/overview')(flatpage_template)
documents              = bp.route('/documents')(flatpage_template)
partners               = bp.route('/partners')(flatpage_template)
energy_tracer_training = bp.route('/energy-tracer-training')(flatpage_template)
management_and_funding = bp.route('/management-and-funding')(flatpage_template)
media_coverage         = bp.route('/media-coverage')(flatpage_template)
publicity_materials    = bp.route('/publicity-materials')(flatpage_template)
