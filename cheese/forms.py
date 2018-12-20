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
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import fields, validators, widgets
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Length, Optional, Required


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


class DatePickerWidget(widgets.TextInput):
    """ A custom date picker widget, using Bootstrap-datetimepicker. """
    def __call__(self, field, **kwargs):
        html = """<div class="input-group date" id="datepicker">
                    <input type="text" class="form-control" %s/>
                      <span class="input-group-addon"></span>
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


class ApplySurveyForm(FlaskForm):
    name = fields.StringField('Name*',
                              validators=[Required(),
                                          Length(max=100)])
    address_line = fields.StringField('Address line*',
                                      validators=[Required(),
                                                  Length(max=100)])
    postcode = fields.StringField('Post code*',
                                  validators=[Required(),
                                              Length(max=10)])
    email = EmailField('Email address*',
                       validators=[Required(),
                                   validators.Email(),
                                   Length(max=100)])
    telephone = fields.StringField('Telephone*',
                                   validators=[Required(),
                                               Length(max=20)])
    mobile = fields.StringField('Mobile',
                                validators=[Optional(),
                                            Length(max=20)])
    availability = fields.TextAreaField('Your availability*',
                                        validators=[Required()])
    num_main_rooms = fields.IntegerField('Number of main rooms ' \
                                         +'(please see <a href="/home-surveys#pricing">pricing details</a>' \
                                         +', this will be confirmed during the survey)*',
                                         validators=[Required()])
    can_heat_comfortably = \
        fields.BooleanField('Can you heat your home to a comfortable ' \
                            +'temperature in the winter?',
                            validators=[Optional()])
    expected_benefit = fields.TextAreaField('How do you think you will ' \
                                            + 'benefit from a survey?',
                                            validators=[Optional()])
    referral = fields.StringField('How did you hear about CHEESE?',
                                  validators=[Optional(),
                                              Length(max=250)])
    free_survey_consideration = \
        fields.BooleanField('I live in a low-income household and ' \
                             +'would like to be considered for a free survey.',
                            validators=[Optional()])
    agree_to_requirements = \
        fields.BooleanField('I <strong>agree</strong> to make the  ' \
            +'<a href="/pre-survey-guide#preparation" target="_blank">'
            +'necessary preparations</a> for the survey and am happy ' \
            +'to <a href="/pre-survey-guide#follow-ups" target="_blank"> ' \
            +'report my progress after one month and one year</a>.',
            validators=[Required()])
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
    def building_type_choices():
      return db_session.query(BuildingTypes).all()
    ward = QuerySelectField('Ward*',
                            validators=[Required()],
                            query_factory=ward_choices,
                            allow_blank=True,
                            blank_text=u'Please select...',)
    building_type = QuerySelectField('Building type',
                                     validators=[Optional()],
                                     query_factory=building_type_choices,
                                     allow_blank=True,
                                     blank_text=u'Please select...',)
    setattr(ApplySurveyForm, 'ward', ward)
    setattr(ApplySurveyForm, 'building_type', building_type)
    return ApplySurveyForm(formdata)

class SubmitResultsForm(FlaskForm):
    lead_surveyor = fields.StringField('Lead surveyor*',
                                       validators=[Required(),
                                       Length(max=50)])
    assistant_surveyor = fields.StringField('Assistant surveyor*',
                                            validators=[Required(),
                                            Length(max=50)])
    householders_name = fields.StringField('Householder\'s name',
                                           validators=[Optional(),
                                                       Length(max=50)])
    address_line = fields.StringField('Address line',
                                      validators=[Length(max=100)])
    survey_date = fields.DateField('Survey date (dd/mm/yyyy)*',
                                   format='%d/%m/%Y',
                                   validators=[Required(),
                                               validate_date],
                                   widget=DatePickerWidget())
    external_temperature = fields.DecimalField('External temperature (C)',
                                               validators=[Optional()])
    loaned_cheese_box = fields.BooleanField('CHEESE box loaned?',
                                            validators=[Optional()])
    cheese_box_number = fields.TextField('CHEESE box number',
					 validators=[Optional(),
						     Length(max=25)])
    year_of_construction = fields.IntegerField('Year of construction',
                                               validators=[Optional()])
    depth_loft_insulation = fields.TextField('Depth of loft insulation (mm)',
					     validators=[Optional(),
							 Length(max=150)])
    number_open_fireplaces = fields.TextField('Number of open fireplaces',
					      validators=[Optional(),
							  Length(max=150)])
    double_glazing = fields.TextField('Amount of double glazing (%)',
				      validators=[Optional(),
						  Length(max=150)])
    num_occupants = fields.IntegerField('Number of occupants',
                                        validators=[Optional()])
    annual_gas_kwh = fields.DecimalField('Annual consumption (kWh',
                                         validators=[Optional()])
    annual_gas_estimated = fields.BooleanField('Is the value based on estimated use?',
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
    annual_elec_kwh = fields.DecimalField('Annual consumption (kWh',
                                           validators=[Optional()])
    annual_elec_estimated = fields.BooleanField('Is the value based on estimated use?',
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
    renewable_contribution_kwh = fields.DecimalField('Annual contribution from renewable generation (kWh)',
                                                     validators=[Optional()])
    faults_identified = fields.TextAreaField('Faults identified*',
                                        validators=[Required()])
    recommendations = fields.TextAreaField('Recommendations*',
                                      validators=[Required()])
    notes = fields.TextAreaField('Notes',
                            validators=[Optional()])


def create_submit_results_form(db_session, formdata):
    """ Dynamicaly create a form to submit results. """
    # Dynamic fields.
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
    survey = QuerySelectField('Survey*',
                               validators=[Required()],
                               query_factory=survey_choices,
                               allow_blank=True,
                               blank_text=u'Please select...')
    building_type = QuerySelectField('Building type',
                                     validators=[Optional()],
                                     query_factory=building_type_choices,
                                     allow_blank=True,
                                     blank_text=u'Please select...')
    wall_construction_type = QuerySelectField('Wall construction',
                                              validators=[Optional()],
                                              query_factory=wall_construction_type_choices,
                                              allow_blank=True,
                                              blank_text=u'Please select...',)
    occupation_type = QuerySelectField('Occupation type',
                                       validators=[Optional()],
                                       query_factory=occupation_type_choices,
                                       allow_blank=True,
                                       blank_text=u'Please select...',)
    primary_heating_type = QuerySelectField('Primary heating type',
                                            validators=[Optional()],
                                            query_factory=space_heating_type_choices,
                                            allow_blank=True,
                                            blank_text=u'Please select...',)
    secondary_heating_type = QuerySelectField('Secondary heating type',
                                              validators=[Optional()],
                                              query_factory=space_heating_type_choices,
                                              allow_blank=True,
                                              blank_text=u'Please select...',)
    water_heating_type = QuerySelectField('Water heating type',
                                          validators=[Optional()],
                                          query_factory=water_heating_type_choices,
                                          allow_blank=True,
                                          blank_text=u'Please select...',)
    cooking_type = QuerySelectField('Cooking type',
                                    validators=[Optional()],
                                    query_factory=cooking_type_choices,
                                    allow_blank=True,
                                    blank_text=u'Please select...',)
    setattr(SubmitResultsForm, 'survey',                 survey)
    setattr(SubmitResultsForm, 'building_type',          building_type)
    setattr(SubmitResultsForm, 'wall_construction_type', wall_construction_type)
    setattr(SubmitResultsForm, 'occupation_type',        occupation_type)
    setattr(SubmitResultsForm, 'primary_heating_type',   primary_heating_type)
    setattr(SubmitResultsForm, 'secondary_heating_type', secondary_heating_type)
    setattr(SubmitResultsForm, 'water_heating_type',     water_heating_type)
    setattr(SubmitResultsForm, 'cooking_type',           cooking_type)
    return SubmitResultsForm(formdata)


class UploadThermalImageForm(FlaskForm):
    image_file = FileField('Image file',
                           validators=[FileRequired(),
                                       FileAllowed(IMAGE_FORMATS,
                                                   'Only images can be uploaded')])
    description = fields.TextAreaField('Description of the image*',
                                       validators=[Required()])
    year_of_construction = fields.IntegerField('Year of construction*',
                                               validators=[Required()])
    keywords = fields.StringField("Keywords (separated by commas ',')*",
                                  validators=[Required()])


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
    householders_name = fields.StringField('Householder\'s name*',
                                           validators=[Required(),
                                                       Length(max=50)])
    address = fields.StringField('Address*',
                                 validators=[Required(),
                                             Length(max=100)])
    annual_gas_kwh = fields.DecimalField('Annual consumption (kWh',
                                         validators=[Optional()])
    annual_gas_estimated = fields.BooleanField('Is the value based on estimated use?',
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
    annual_elec_kwh = fields.DecimalField('Annual consumption (kWh',
                                          validators=[Optional()])
    annual_elec_estimated = fields.BooleanField('Is the value based on estimated use?',
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
    completed_actions = fields.TextAreaField('Have you already taken action to improve the thermal efficiency of your home?*',
                                             description='If so, then what have you done?',
                                             validators=[Required()])
    planned_actions = fields.TextAreaField('What you are planning to do to in the next few years improve the thermal efficiency of your home?*',
                                           description='This can be anything from draught proofing to installing external wall insulation.',
                                           validators=[Required()])
    choices_1_to_5 = [choice(str(x)) for x in range(1,6)]
    satisfaction_1to5 = fields.RadioField('How satisified were you with the survey overall? (1: least, to 5: most)*',
                                          widget=OneToFiveWidget(),
                                          choices=choices_1_to_5,
                                          validators=[Required()])
    cheese_box_1to5 = fields.RadioField('How useful did you find the CHEESE box? (1: least, to 5: most)*',
                                        widget=OneToFiveWidget(),
                                        choices=choices_1_to_5,
                                        validators=[Required()])
    survey_video_1to5 = fields.RadioField('How useful have you find the survey video? (1: not at all, to 5: very)*',
                                          widget=OneToFiveWidget(),
                                          choices=choices_1_to_5,
                                          validators=[Required()])
    surveyor_conduct_1to5 = fields.RadioField('How was the conduct of the surveyor? (1: poor, to 5: excellent)*',
                                              widget=OneToFiveWidget(),
                                              choices=choices_1_to_5,
                                              validators=[Required()])
    survey_value_1to5 = fields.RadioField('Was the survey good value for money? (1: disagree, to 5: agree)*',
                                          widget=OneToFiveWidget(),
                                          choices=choices_1_to_5,
                                          validators=[Required()])
    recommend_1to5 = fields.RadioField('Are you likely to recommend the survey to a friend or neighbour? (1: unlikely, to 5: definitely)*',
                                       widget=OneToFiveWidget(),
                                       choices=choices_1_to_5,
                                       validators=[Required()])
    cheese_box = fields.TextAreaField('Can you explain your <a href="/cheese-box">CHEESE box</a> score?*',
                                      description='We would be interested to know specifically what you found useful and what you didn\'t.',
                                      validators=[Required()])
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
    householders_name = fields.StringField('Householder\'s name*',
                                           validators=[Required(),
                                                       Length(max=50)])
    address = fields.StringField('Address*',
                                 validators=[Required(),
                                             Length(max=100)])
    annual_gas_kwh = fields.DecimalField('Annual consumption (kWh',
                                         validators=[Optional()])
    annual_gas_estimated = fields.BooleanField('Is the value based on estimated use?',
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
    annual_elec_kwh = fields.DecimalField('Annual consumption (kWh',
                                          validators=[Optional()])
    annual_elec_estimated = fields.BooleanField('Is the value based on estimated use?',
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
    diy_work = fields.TextAreaField('What work have you done yourself?*',
                                    validators=[Required()])
    prof_work = fields.TextAreaField('What work have you paid for to be done professionally?*',
                                     validators=[Required()])
    contractors_used = fields.TextAreaField('If you had work done professionally, which contractors did you use?',
                                            description='And were these contractors based in Bristol or from further afield?',
                                            validators=[Optional()])
    total_spent = fields.DecimalField('Approximately how much have you spent in total on energy improvements to your home?',
                                      description='Only answer this if you feel comfortable to.',
                                      validators=[Optional()])
    total_spent_diy = fields.DecimalField('Approximately how much did you spend on DIY?',
                                          validators=[Optional()])
    total_spent_local = fields.DecimalField('Approximately how much did you spend on local contractors?',
                                            validators=[Optional()])
    planned_work = fields.TextAreaField('Do you have any further work planned? And, if so, what?*',
                                        validators=[Required()])
    wellbeing_improvement = fields.TextAreaField('Have the actions you\'ve taken made your house feel warmer?',
                                                 description='Perhaps even if you haven\'t saved any money on your bills!',
                                                 validators=[Optional()])
    behaviour_temperature = fields.TextAreaField('Has the period and temperature you use the heating for changed, and if so, how?*',
                                                 validators=[Required()])
    behaviour_space = fields.TextAreaField('Do you use space in your home differently now, and if so, how?*',
                                           validators=[Required()])
    behaviour_changes = fields.TextAreaField('How else has your behaviour changed after the survey?*',
                                             validators=[Required()])
    feedback = fields.TextAreaField('Lastly, do you have any other feedback on the CHEESE Project?',
                                    description='We would like to hear what you think about:'
                                                  +' how useful the survey was,'
                                                  +' how useful the <a href="/cheese-box">CHEESE box</a> was,'
                                                  +' your overall satisfaction,'
                                                  +' and anything else at all you would like to let us know.',
                                    validators=[Optional()])

class MembershipForm(FlaskForm):
    name = fields.StringField('Organisation name or name of individual if individual membership*',
                              validators=[Required(),
                                          Length(max=250)])
    address = fields.StringField('Address*',
                                 validators=[Required(),
                                             Length(max=500)])
    email = fields.StringField('Contact email address*',
                               description='This will act as the primary point of contact',
                               validators=[Required(),
                                           Length(max=100)])
    telephone = fields.StringField('Contact telephone number*',
                                   validators=[Required(),
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
