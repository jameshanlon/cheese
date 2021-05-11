import datetime
from cheese.models import Surveys, \
                          Wards, \
                          BuildingTypes, \
                          WallConstructionTypes, \
                          OccupationTypes, \
                          SpaceHeatingTypes, \
                          WaterHeatingTypes, \
                          CookingTypes
from cheese.settings import IMAGE_FORMATS
from flask import Markup
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import fields, validators, widgets
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Length, Optional, DataRequired, InputRequired, NumberRange


def choice(string):
    return (string, string)


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


class RequiredIf(InputRequired):
    """
    Validator which makes a field required if another field is set and has a truthy value.
    Sources:
        - http://wtforms.simplecodes.com/docs/1.0.1/validators.html
        - http://stackoverflow.com/questions/8463209/how-to-make-a-field-conditionally-optional-in-wtforms
    """
    field_flags = ('requiredif',)

    def __init__(self, other_field_name, message=None, *args, **kwargs):
        self.other_field_name = other_field_name
        self.message = message

    def __call__(self, form, field):
        other_field = form[self.other_field_name]
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if bool(other_field.data):
            super(RequiredIf, self).__call__(form, field)
        else:
            Optional().__call__(form, field)

date_picker_id = 0

class DatePickerWidget(widgets.TextInput):
    """ A custom date picker widget, using Bootstrap-datetimepicker. """
    def __init__(self):
         super(DatePickerWidget, self).__init__()
         global date_picker_id
         self.date_picker_id = date_picker_id
         date_picker_id += 1
    def __call__(self, field, **kwargs):
        if kwargs.get('is_invalid', False):
            html = """<div class="input-group date datepicker" id="datepicker-{0}">
                        <input type="text" {1} {2}>
                        <span class="input-group-addon"></span>
                         <div class="invalid-feedback">Please select a valid date.</div> 
                       </div>"""
        else:
            html = """<div class="input-group date datepicker" id="datepicker-{0}">
                        <input type="text" {1} {2}>
                        <span class="input-group-addon"></span>
                       </div>"""
        return Markup(html.format(self.date_picker_id,
                                  'value={}'.format(field.data.strftime('%d/%m/%Y')) if field.data else '',
                                  self.html_params(name=field.name, **kwargs)))


class OneToFiveWidget(widgets.Input):
    """ A custom widget for 1-to-5 ratings. """
    def __call__(self, field, **kwargs):
        field_1_checked = 'checked' if field.data and field.data == '1' else ''
        field_2_checked = 'checked' if field.data and field.data == '2' else ''
        field_3_checked = 'checked' if field.data and field.data == '3' else ''
        field_4_checked = 'checked' if field.data and field.data == '4' else ''
        field_5_checked = 'checked' if field.data and field.data == '5' else ''
        html = """<div class="custom-control custom-radio custom-control-inline">
                    <input type="radio" id="{0}-1" name="{0}" value="1" {1} {6}>
                    <label class="custom-control-label" for="{0}-1">1</label>
                  </div>
                  <div class="custom-control custom-radio custom-control-inline">
                    <input type="radio" id="{0}-2" name="{0}" value="2" {2} {6}>
                    <label class="custom-control-label" for="{0}-2">2</label>
                  </div>
                  <div class="custom-control custom-radio custom-control-inline">
                    <input type="radio" id="{0}-3" name="{0}" value="3" {3} {6}>
                    <label class="custom-control-label" for="{0}-3">3</label>
                  </div>
                  <div class="custom-control custom-radio custom-control-inline">
                    <input type="radio" id="{0}-4" name="{0}" value="4" {4} {6}>
                    <label class="custom-control-label" for="{0}-4">4</label>
                  </div>
                  <div class="custom-control custom-radio custom-control-inline">
                    <input type="radio" id="{0}-5" name="{0}" value="5" {5} {6}>
                    <label class="custom-control-label" for="{0}-5">5</label>
                  </div>"""
        return Markup(html.format(field.name,
                                  field_1_checked,
                                  field_2_checked,
                                  field_3_checked,
                                  field_4_checked,
                                  field_5_checked,
                                  self.html_params(**kwargs)))


class ApplySurveyForm(FlaskForm):
    recaptcha = RecaptchaField()
    name = \
        fields.StringField('Name*',
                           validators=[DataRequired(),
                                       Length(max=100)])
    address_line = \
        fields.StringField('Address line*',
                            validators=[DataRequired(),
                                        Length(max=100)])
    postcode = \
        fields.StringField('Post code*',
                           validators=[DataRequired(),
                                       Length(max=10)])
    email = \
        EmailField('Email address*',
                   validators=[DataRequired(),
                               validators.Email(),
                               Length(max=100)])
    telephone = \
        fields.StringField('Main contact telephone number*',
                           validators=[DataRequired(),
                                       Length(max=20)])
    mobile = \
        fields.StringField('Secondary contact telephone number',
                           validators=[Optional(),
                                       Length(max=20)])
    num_main_rooms = \
        fields.IntegerField('Number of main rooms* ' \
                            +'(please see <a href="/home-surveys#pricing">pricing details</a>' \
                            +', this will be confirmed during the survey)*',
                            validators=[DataRequired(),
                                        NumberRange(min=1, max=100)])
    can_heat_comfortably = \
        fields.BooleanField('(tick for yes) Can you heat your home to a comfortable ' \
                            +'temperature in the winter?',
                            validators=[Optional()])
    expected_benefit = \
        fields.TextAreaField('How do you think you will benefit from a survey?*',
                             validators=[DataRequired()])
    has_asbestos = \
        fields.BooleanField('(tick for yes) Are you aware of any asbestos, exposed or not exposed, in the building?',
                            validators=[Optional()])
    asbestos_details = \
        fields.TextAreaField('If yes, please give details',
                             validators=[RequiredIf('has_asbestos')])
    availability = \
        fields.TextAreaField('What is your availability to schedule the survey?*',
                             description='Please see the <a href="/home-surveys">survey information</a> for the expected duration of your survey.',
                             validators=[DataRequired()])
    referral = \
        fields.StringField('How did you hear about C.H.E.E.S.E. thermal-imaging surveys?',
                           validators=[Optional(),
                                       Length(max=250)])
    free_survey_consideration = \
        fields.BooleanField('(tick for yes) I would like to be considered for a free survey. ' \
                              +' We are working with partners to make free surveys' \
                              +' available to people in poor housing conditions ' \
                              +' and / or fuel poverty. Please tick the box if ' \
                              +' you think this applies to your situation. You can talk this ' \
                              +' through with our survey manager when they contact you.',
                            validators=[Optional()])
    special_considerations = \
        fields.TextAreaField('Do you have any special requirements that we need to be aware of during the survey?',
                             description='<ul class="text-muted">' \
                                         +'<li>Do you have any illnesses or disabilities?</li>' \
                                         +'<li>Will you be able to accompany the surveyor around your home for two to three hours during the survey?</li>' \
                                         +'<li>Do you have any pets that will be present in your home during the survey?</li>' \
                                         +'</ul>',
                             validators=[Optional()])
    agree_to_requirements = \
        fields.BooleanField(
""" I <strong>agree</strong> to make the <a
href="/pre-survey-guide#preparation" target="_blank"> necessary
preparations</a> for the survey, and I am <strong>happy</strong> to <a
href="/pre-survey-guide#follow-ups" target="_blank">report my progress</a>
after one month, and after one and two years after the survey. """,
            validators=[DataRequired()])
    agree_to_cancellation = \
        fields.BooleanField(
""" I have <strong>read and understood</strong> the <a
href="/home-surveys#cancellation" target="_blank">cancellation policy</a>: if
your survey is cancelled less than 72 hours (3 days) prior to your survey there
will be a &pound;100 cancellation fee. If you rebook your survey for a
different date in the same season, &pound;50 of this will be credited against
your new booking. """,
            validators=[DataRequired()])
    photo_release = \
        fields.BooleanField('I <strong>agree</strong> to any of the ' \
            +'still photos to be taken during my survey that do not ' \
            +'clearly identify a specific person or place to be used in a ' \
            +'publicly-accessible record on thermal faults and energy ' \
            +'efficiency.')

def create_apply_survey_form(db_session, formdata):
    """ Dynamicaly create a form to apply for a survey. """
    def ward_choices():
      return db_session.query(Wards).all()
    ward = QuerySelectField('Ward*',
                            validators=[DataRequired()],
                            query_factory=ward_choices,
                            allow_blank=True,
                            blank_text=u'Please select...',)
    setattr(ApplySurveyForm, 'ward', ward)
    return ApplySurveyForm(formdata)


class PreSurveyDetailsForm(FlaskForm):
    recaptcha = RecaptchaField()
    year_of_construction = \
        fields.IntegerField('Year of construction',
                            validators=[Optional(),
                                        NumberRange(min=1000,
                                                    max=datetime.datetime.now().year)])
    depth_loft_insulation = \
        fields.TextField('Depth of loft insulation (mm)',
                         validators=[Optional(),
                                     Length(max=150)])
    number_open_fireplaces = \
        fields.TextField('Number of open fireplaces',
                         validators=[Optional(),
                                     Length(max=150)])
    double_glazing = \
        fields.TextField('Amount of double glazing (%)',
                         validators=[Optional(),
                                     Length(max=150)])
    num_occupants = \
        fields.IntegerField('Number of occupants',
                            validators=[Optional(),
                                        NumberRange(min=1, max=100)])
    annual_gas_kwh = \
        fields.DecimalField('Annual consumption (kWh',
                            validators=[Optional()])
    annual_gas_estimated = \
        fields.BooleanField('(tick for yes) Is the value based on estimated use?',
                            validators=[Optional()])
    annual_gas_start_date = \
        fields.DateField('Start date (dd/mm/yyyy)',
                         format='%d/%m/%Y',
                         validators=[Optional(),
                         validate_date],
                         widget=DatePickerWidget())
    annual_gas_end_date = \
        fields.DateField('End date (dd/mm/yyyy)',
                         format='%d/%m/%Y',
                         validators=[Optional(),
                         validate_date],
                         widget=DatePickerWidget())
    annual_elec_kwh = \
        fields.DecimalField('Annual consumption (kWh',
                            validators=[Optional()])
    annual_elec_estimated = \
        fields.BooleanField('(tick for yes) Is the value based on estimated use?',
                            validators=[Optional()])
    annual_elec_start_date = \
        fields.DateField('Start date (dd/mm/yyyy)',
                         format='%d/%m/%Y',
                         validators=[Optional(),
                         validate_date],
                         widget=DatePickerWidget())
    annual_elec_end_date = \
        fields.DateField('End date (dd/mm/yyyy)',
                         format='%d/%m/%Y',
                         validators=[Optional(),
                         validate_date],
                         widget=DatePickerWidget())
    annual_solid_spend = \
        fields.DecimalField('Annual spend on solid fuels (&pound;)',
                            validators=[Optional()])
    renewable_contribution_kwh = \
        fields.DecimalField('Annual contribution from renewable generation (kWh)',
                            validators=[Optional()])
    notes = \
          fields.TextAreaField('Notes (any other relevant information)',
                               validators=[Optional()])

def add_dynamic_fields_to_pre_survey_details_form(db_session):
    def survey_choices():
      return db_session.query(Surveys).all()
    def building_type_choices():
      return db_session.query(BuildingTypes).all()
    def wall_construction_type_choices():
      return db_session.query(WallConstructionTypes).all()
    def occupation_type_choices():
      return db_session.query(OccupationTypes).all()
    def space_heating_type_choices():
      return db_session.query(SpaceHeatingTypes).all()
    def water_heating_type_choices():
      return db_session.query(WaterHeatingTypes).all()
    def cooking_type_choices():
      return db_session.query(CookingTypes).all()
    survey = \
        QuerySelectField('Survey*',
                         validators=[DataRequired()],
                         query_factory=survey_choices,
                         allow_blank=True,
                         blank_text=u'Please select...')
    building_type = \
        QuerySelectField('Building type',
                         validators=[Optional()],
                         query_factory=building_type_choices,
                         allow_blank=True,
                         blank_text=u'Please select...')
    wall_construction_type = \
        QuerySelectField('Wall construction',
                         validators=[Optional()],
                         query_factory=wall_construction_type_choices,
                         allow_blank=True,
                         blank_text=u'Please select...',)
    occupation_type = \
        QuerySelectField('Occupation type',
                         validators=[Optional()],
                         query_factory=occupation_type_choices,
                         allow_blank=True,
                         blank_text=u'Please select...',)
    primary_heating_type = \
        QuerySelectField('Primary heating type',
                         validators=[Optional()],
                         query_factory=space_heating_type_choices,
                         allow_blank=True,
                         blank_text=u'Please select...',)
    secondary_heating_type = \
        QuerySelectField('Secondary heating type',
                         validators=[Optional()],
                         query_factory=space_heating_type_choices,
                         allow_blank=True,
                         blank_text=u'Please select...',)
    water_heating_type = \
        QuerySelectField('Water heating type',
                         validators=[Optional()],
                         query_factory=water_heating_type_choices,
                         allow_blank=True,
                         blank_text=u'Please select...',)
    cooking_type = \
        QuerySelectField('Cooking type',
                         validators=[Optional()],
                         query_factory=cooking_type_choices,
                         allow_blank=True,
                         blank_text=u'Please select...',)
    setattr(PreSurveyDetailsForm, 'survey',                 survey)
    setattr(PreSurveyDetailsForm, 'building_type',          building_type)
    setattr(PreSurveyDetailsForm, 'wall_construction_type', wall_construction_type)
    setattr(PreSurveyDetailsForm, 'occupation_type',        occupation_type)
    setattr(PreSurveyDetailsForm, 'primary_heating_type',   primary_heating_type)
    setattr(PreSurveyDetailsForm, 'secondary_heating_type', secondary_heating_type)
    setattr(PreSurveyDetailsForm, 'water_heating_type',     water_heating_type)
    setattr(PreSurveyDetailsForm, 'cooking_type',           cooking_type)

def create_pre_survey_details_et_form(db_session, formdata):
    """ Dynamicaly create a form to submit results. """
    # Dynamic fields.
    add_dynamic_fields_to_pre_survey_details_form(db_session)
    return PreSurveyDetailsForm(formdata)


def create_pre_survey_details_form(db_session, formdata):
    # Public version of the pre details form.
    add_dynamic_fields_to_pre_survey_details_form(db_session)
    delattr(PreSurveyDetailsForm, 'survey')
    # Add these additional fields.
    householders_name = fields.StringField('Your name*',
                                                validators=[Optional(),
                                                            Length(max=50)])
    address_line = fields.StringField('Address line*',
                                      validators=[Optional(),
                                                  Length(max=100)])
    postcode = fields.StringField('Post code*',
                                   validators=[Optional(),
                                           Length(max=10)])
    setattr(PreSurveyDetailsForm, 'householders_name', householders_name)
    setattr(PreSurveyDetailsForm, 'address_line', address_line) 
    setattr(PreSurveyDetailsForm, 'postcode', postcode)
    return PreSurveyDetailsForm(formdata)

class PostSurveyDetailsForm(FlaskForm):
    recaptcha = RecaptchaField()
    lead_surveyor = \
        fields.StringField('Lead surveyor*',
                           validators=[DataRequired(),
                                       Length(max=50)])
    assistant_surveyor = \
        fields.StringField('Assistant surveyor*',
                           validators=[DataRequired(),
                           Length(max=50)])
    survey_date = \
        fields.DateField('Survey date (dd/mm/yyyy)*',
                         format='%d/%m/%Y',
                         validators=[DataRequired(),
                                     validate_date],
                         widget=DatePickerWidget())
    external_temperature = \
        fields.DecimalField('External temperature (C)',
                            validators=[Optional()])
    camera_kit_number = \
        fields.TextField('Camera kit number*',
                         validators=[DataRequired(),
                                     Length(max=25)])
    faults_identified = \
        fields.TextAreaField('Faults identified',
                             validators=[Optional()])
    recommendations = \
        fields.TextAreaField('Recommendations',
                             validators=[Optional()])
    notes = \
          fields.TextAreaField('Notes (any other relevant information)',
                               validators=[Optional()])


def create_post_survey_details_form(db_session, formdata):
    """ Dynamicaly create a form to submit results. """
    # Dynamic fields.
    def survey_choices():
      return db_session.query(Surveys).all()
    survey = \
        QuerySelectField('Survey*',
                         validators=[DataRequired()],
                         query_factory=survey_choices,
                         allow_blank=True,
                         blank_text=u'Please select...')
    setattr(PostSurveyDetailsForm, 'survey', survey)
    return PostSurveyDetailsForm(formdata)


class UploadThermalImageForm(FlaskForm):
    image_file = FileField('Image file',
                           validators=[FileRequired(),
                                       FileAllowed(IMAGE_FORMATS,
                                                   'Only images can be uploaded')])
    description = fields.TextAreaField('Description of the image*',
                                       validators=[DataRequired()])
    year_of_construction = fields.IntegerField('Year of construction',
                                               validators=[Optional()])
    keywords = fields.StringField("Keywords (separated by commas ',')*",
                                  validators=[DataRequired()])


def create_upload_thermal_image_form(db_session, formdata=None):
    """
    Dynamicaly create a form to apply for a survey. Note that the FlaskForm is
    not initialised with formdata since this prevents the underlying
    FileStorage object from being initialised and the POSTed image data being
    ignored. See
    https://stackoverflow.com/questions/19203343/flask-wtf-filefield-does-not-set-data-attribute-to-an-instance-of-werkzeug-files
    """
    def building_type_choices():
      return db_session.query(BuildingTypes).all()
    building_type = QuerySelectField('Building type',
                                     validators=[Optional()],
                                     query_factory=building_type_choices,
                                     allow_blank=True,
                                     blank_text=u'Please select...',)
    setattr(UploadThermalImageForm, 'building_type', building_type)
    return UploadThermalImageForm()


class OneMonthFeedbackForm(FlaskForm):
    not_needed = 'We only need this if we didn\'t collect this during the survey.'
    numbers_only = 'Only use digits and (optionally) a decimal point, no other punctuation or symbols.'
    recaptcha = RecaptchaField()
    householders_name = fields.StringField('Householder\'s name*',
                                           validators=[DataRequired(),
                                                       Length(max=50)])
    address = fields.StringField('Address*',
                                 validators=[DataRequired(),
                                             Length(max=100)])
    annual_gas_kwh = fields.DecimalField('Annual consumption (kWh)',
                                         validators=[Optional()])
    annual_gas_estimated = fields.BooleanField('(tick for yes) Is the value based on estimated use?',
                                               validators=[Optional()])
    annual_gas_start_date = fields.DateField('Start date (dd/mm/yyyy)',
                                             format='%d/%m/%Y',
                                             validators=[Optional(),
                                             validate_date],
                                             widget=DatePickerWidget())
    annual_gas_end_date = fields.DateField('End date (dd/mm/yyyy)',
                                           format='%d/%m/%Y',
                                           validators=[Optional(),
                                           validate_date],
                                           widget=DatePickerWidget())
    annual_elec_kwh = fields.DecimalField('Annual consumption (kWh)',
                                          validators=[Optional()])
    annual_elec_estimated = fields.BooleanField('(tick for yes) Is the value based on estimated use?',
                                                validators=[Optional()])
    annual_elec_start_date = fields.DateField('Start date (dd/mm/yyyy)',
                                              format='%d/%m/%Y',
                                              validators=[Optional(),
                                              validate_date],
                                              widget=DatePickerWidget())
    annual_elec_end_date = fields.DateField('End date (dd/mm/yyyy)',
                                            format='%d/%m/%Y',
                                            validators=[Optional(),
                                            validate_date],
                                            widget=DatePickerWidget())
    annual_solid_spend = fields.DecimalField('Annual spend on solid fuels (&pound;)',
                                             validators=[Optional()])
    renewable_contrib_kwh = fields.DecimalField('Annual contribution from renewable generation (kWh)',
                                                validators=[Optional()])
    any_completed_actions = fields.BooleanField('(tick for yes) Have you already taken action to improve the thermal efficiency of your home?',
                                                validators=[Optional()])
    completed_actions = fields.TextAreaField('If so, then what have you done? And have you done the work yourself or has it been done professionally?',
                                             validators=[RequiredIf('any_completed_actions')])
    any_planned_work = fields.BooleanField('(tick for yes) Are you planning to do remedial work in the next few years?',
                                           validators=[Optional()])
    planned_actions = fields.TextAreaField('If so, then what are you planning?',
                                           description='This can be anything from draught proofing to installing external wall insulation.',
                                           validators=[RequiredIf('any_planned_work')])
    any_wellbeing_improvement = fields.BooleanField('(tick for yes) Have the actions you\'ve taken made your house feel warmer?',
                                                    validators=[Optional()])
    wellbeing_improvement = fields.TextAreaField('If so, then how? (Even if perhaps you haven\'t saved money on your bills.)',
                                                 validators=[RequiredIf('any_wellbeing_improvement')])
    any_behaviour_change = fields.BooleanField('(tick for yes) Has your behaviour changed as a result of your survey?',
                                               validators=[Optional()])
    behaviour_temperature = fields.TextAreaField('How has the period and temperature you use the heating for changed? (if at all)',
                                                 validators=[RequiredIf('any_behaviour_change')])
    behaviour_space = fields.TextAreaField('How do you use space in your home differently? (if at all)',
                                           validators=[RequiredIf('any_behaviour_change')])
    behaviour_changes = fields.TextAreaField('In what other ways has your behaviour changed after the survey?',
                                             validators=[RequiredIf('any_behaviour_change')])
    choices_1_to_5 = [choice(str(x)) for x in range(1,6)]
    satisfaction_1to5 = fields.RadioField('How satisified were you with the survey overall? (1: least, to 5: most)*',
                                          widget=OneToFiveWidget(),
                                          choices=choices_1_to_5,
                                          validators=[DataRequired()])
    survey_video_1to5 = fields.RadioField('How useful have you find the survey video? (1: not at all, to 5: very)*',
                                          widget=OneToFiveWidget(),
                                          choices=choices_1_to_5,
                                          validators=[DataRequired()])
    surveyor_conduct_1to5 = fields.RadioField('How was the conduct of the surveyor? (1: poor, to 5: excellent)*',
                                              widget=OneToFiveWidget(),
                                              choices=choices_1_to_5,
                                              validators=[DataRequired()])
    survey_value_1to5 = fields.RadioField('Was the survey good value for money? (1: disagree, to 5: agree)*',
                                          widget=OneToFiveWidget(),
                                          choices=choices_1_to_5,
                                          validators=[DataRequired()])
    recommend_1to5 = fields.RadioField('Are you likely to recommend the survey to a friend or neighbour? (1: unlikely, to 5: definitely)*',
                                       widget=OneToFiveWidget(),
                                       choices=choices_1_to_5,
                                       validators=[DataRequired()])
    feedback = fields.TextAreaField('Do you have any feedback?',
                                    description='We would like to hear what you think about:'
                                                   +' the organisation of the survey,'
                                                   +' the conduct of the Energy Tracers,'
                                                   +' the results of the survey and suggested remedies,'
                                                   +' the overall value for money of the survey,'
                                                   +' your overall satisfaction,'
                                                   +' and anything else at all you would like to let us know.',
                                    validators=[Optional()])


class OneYearFeedbackForm(FlaskForm):
    numbers_only = 'Only use digits and (optionally) a decimal point, no other punctuation or symbols.'
    #recaptcha = RecaptchaField()
    householders_name = fields.StringField('Householder\'s name*',
                                           validators=[DataRequired(),
                                                       Length(max=50)])
    address = fields.StringField('Address*',
                                 validators=[DataRequired(),
                                             Length(max=100)])
    annual_gas_kwh = fields.DecimalField('Annual consumption (kWh)',
                                         validators=[Optional()])
    annual_gas_estimated = fields.BooleanField('(tick for yes) Is the value based on estimated use?',
                                               validators=[Optional()])
    annual_gas_start_date = fields.DateField('Start date (dd/mm/yyyy)',
                                             format='%d/%m/%Y',
                                             validators=[Optional(),
                                             validate_date],
                                             widget=DatePickerWidget())
    annual_gas_end_date = fields.DateField('End date (dd/mm/yyyy)',
                                           format='%d/%m/%Y',
                                           validators=[Optional(),
                                           validate_date],
                                           widget=DatePickerWidget())
    annual_elec_kwh = fields.DecimalField('Annual consumption (kWh)',
                                          validators=[Optional()])
    annual_elec_estimated = fields.BooleanField('(tick for yes) Is the value based on estimated use?',
                                                validators=[Optional()])
    annual_elec_start_date = fields.DateField('Start date (dd/mm/yyyy)',
                                              format='%d/%m/%Y',
                                              validators=[Optional(),
                                              validate_date],
                                              widget=DatePickerWidget())
    annual_elec_end_date = fields.DateField('End date (dd/mm/yyyy)',
                                            format='%d/%m/%Y',
                                            validators=[Optional(),
                                            validate_date],
                                            widget=DatePickerWidget())
    annual_solid_spend = fields.DecimalField('Annual spend on solid fuels (&pound;)',
                                             validators=[Optional()])
    renewable_contrib_kwh = fields.DecimalField('Annual contribution from renewable generation (kWh)',
                                                validators=[Optional()])
    any_completed_actions = fields.BooleanField('(tick for yes) Have you taken action since your survey ' \
                                                +'to improve the thermal efficiency of your home?*',
                                                validators=[Optional()])
    diy_work = fields.TextAreaField('What work have you done yourself?*',
                                    validators=[RequiredIf('any_completed_actions')])
    prof_work = fields.TextAreaField('And, what work, if any, have you paid for to be done professionally?*',
                                     validators=[RequiredIf('any_completed_actions')])
    contractors_used = fields.TextAreaField('If you had work done professionally, which contractors did you use?',
                                            description='And were these contractors based in Bristol or from further afield?',
                                            validators=[Optional('any_completed_actions')])
    total_spent = fields.DecimalField('Approximately how much have you spent in total on energy improvements to your home? (&pound;)',
                                      description='Only answer this if you feel comfortable to.',
                                      validators=[Optional()])
    total_spent_diy = fields.DecimalField('Approximately how much did you spend on DIY? (&pound;)',
                                          validators=[Optional()])
    total_spent_local = fields.DecimalField('Approximately how much did you spend on local contractors? (&pound;)',
                                            validators=[Optional()])
    non_homeowner_work = fields.TextAreaField('If you are a low-income household or do not own your home, have you asked ' \
                                              +'the council, your housing association or your landlord to make any changes ' \
                                              +'to your home following the survey?  If so, what was their response?',
                                              validators=[Optional()])
    any_planned_work = fields.BooleanField('(tick for yes) Do you have any future work planned?',
                                           validators=[Optional()])
    planned_work = fields.TextAreaField('If so, what are you planning?*',
                                        validators=[RequiredIf('any_planned_work')])
    any_wellbeing_improvement = fields.BooleanField('(tick for yes) Have the actions you\'ve taken made your house feel warmer?',
                                                    validators=[Optional()])
    wellbeing_improvement = fields.TextAreaField('If so, then how? (Even if perhaps you haven\'t saved money on your bills.)',
                                                 validators=[RequiredIf('any_wellbeing_improvement')])
    any_behaviour_change = fields.BooleanField('(tick for yes) Has your behaviour changed as a result of your survey?',
                                               validators=[Optional()])
    behaviour_temperature = fields.TextAreaField('How has the period and temperature you use the heating for changed? (if at all)',
                                                 validators=[RequiredIf('any_behaviour_change')])
    behaviour_space = fields.TextAreaField('How do you use space in your home differently? (if at all)',
                                           validators=[RequiredIf('any_behaviour_change')])
    behaviour_changes = fields.TextAreaField('In what other ways has your behaviour changed after the survey?',
                                             validators=[RequiredIf('any_behaviour_change')])
    feedback = fields.TextAreaField('Lastly, do you have any other feedback on the CHEESE Project?',
                                    description='We would like to hear what you think about:'
                                                  +' how useful the survey was,'
                                                  +' your overall satisfaction,'
                                                  +' and anything else at all you would like to let us know.',
                                    validators=[Optional()])

class MembershipForm(FlaskForm):
    recaptcha = RecaptchaField()
    name = fields.StringField('Organisation name or name of individual if individual membership*',
                              validators=[DataRequired(),
                                          Length(max=250)])
    address = fields.StringField('Address*',
                                 validators=[DataRequired(),
                                             Length(max=500)])
    email = fields.StringField('Contact email address*',
                               description='This will act as the primary point of contact',
                               validators=[DataRequired(),
                                           Length(max=100)])
    telephone = fields.StringField('Contact telephone number*',
                                   validators=[DataRequired(),
                                               Length(max=20)])
    representative_1_name = fields.StringField('Name',
                                               validators=[Optional(),
                                                           Length(max=100)])
    representative_1_email = fields.StringField('Contact email address',
                                                validators=[Optional(),
                                                            Length(max=100)])
    representative_1_telephone = fields.StringField('Contact telephone number',
                                                    validators=[Optional(),
                                                                Length(max=100)])
    representative_2_name = fields.StringField('Name',
                                               validators=[Optional(),
                                                           Length(max=100)])
    representative_2_email = fields.StringField('Contact email address',
                                                validators=[Optional(),
                                                            Length(max=100)])
    representative_2_telephone = fields.StringField('Contact telephone number',
                                                    validators=[Optional(),
                                                                Length(max=100)])
