import datetime
import os
import pytest
import tempfile
from io import BytesIO
from cheese.factory import create_app
from cheese.models import db, \
                          User, \
                          BuildingTypes, \
                          WallConstructionTypes, \
                          OccupationTypes, \
                          SpaceHeatingTypes, \
                          WaterHeatingTypes, \
                          CookingTypes, \
                          Wards, \
                          Surveys, \
                          Results, \
                          MonthFeedback, \
                          YearFeedback, \
                          Member, \
                          ThermalImage
from cheese.commands import resetdb
from flask_login import login_user

@pytest.fixture
def app():
    config = dict(
      FLASK_DEBUG=True,
      WTF_CSRF_ENABLED = False,
      SQLALCHEMY_DATABASE_URI = 'sqlite:///' + \
          tempfile.NamedTemporaryFile(suffix='.db').name,
      MAIL_SUPPRESS_SEND = True, )
    app = create_app(config)
    app.testing = True
    print 'Using db '+app.config['SQLALCHEMY_DATABASE_URI']
    with app.app_context():
        resetdb()
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def login(client, username, password):
    return client.post('/user/sign-in',
                       data=dict(email=username,
                                 password=password),
                       follow_redirects=True)

def logout(client):
    return client.get('/user/sign-out', follow_redirects=True)

def admin_login(client):
    return login(client, 'admin@cheeseproject.co.uk', 'admin')

def test_user_login(client, app):
    rv = admin_login(client)
    assert b'Incorrect Password' not in rv.data
    rv = logout(client)

# Tests the form submits with valid input data.
def test_apply_for_survey_form(client, app):
    rv = client.post('/apply-for-a-survey', data=dict(
             name                      = 'test_name',
             address_line              = 'address_line',
             postcode                  = 'postcode',
             ward                      = 1,
             email                     = 'name@domain.com',
             telephone                 = '1234567',
             mobile                    = '1234567',
             availability              = 'availability',
             building_type             = 1,
             num_main_rooms            = '1',
             can_heat_comfortably      = 'True',
             expected_benefit          = 'expected_benefit',
             referral                  = 'referral',
             free_survey_consideration = 'True',
             special_considerations    = 'special_considerations',
             agree_to_requirements     = 'True', # Not stored in DB.
             photo_release             = 'True',
          ), follow_redirects=True)
    assert b'Your survey application has been sent' in rv.data
    with app.app_context():
        survey = Surveys.query.filter(Surveys.name=='test_name').first()
        assert survey.name                      == 'test_name'
        assert survey.address_line              == 'address_line'
        assert survey.postcode                  == 'postcode'
        assert survey.ward                      == Wards.query.get(1)
        assert survey.email                     == 'name@domain.com'
        assert survey.telephone                 == '1234567'
        assert survey.mobile                    == '1234567'
        assert survey.availability              == 'availability'
        assert survey.building_type             == BuildingTypes.query.get(1)
        assert survey.num_main_rooms            == 1
        assert survey.can_heat_comfortably      == True
        assert survey.expected_benefit          == 'expected_benefit'
        assert survey.referral                  == 'referral'
        assert survey.free_survey_consideration == True
        assert survey.special_considerations    == 'special_considerations'
        assert survey.photo_release             == True


# Tests the form submits with valid input data.
def test_submit_results_form(client, app):
    rv = admin_login(client)
    rv = client.post('/submit-results', data=dict(
	     survey                     = 1,
	     lead_surveyor              = 'test_lead_surveyor',
	     assistant_surveyor         = 'assistant_surveyor',
	     householders_name          = 'householders_name',
	     address_line               = 'address_line',
	     survey_date                = '01/02/2017',
	     external_temperature       = 123.456,
	     loaned_cheese_box          = True,
	     cheese_box_number          = 'Box 42',
	     year_of_construction       = 1970,
	     building_type              = '1',
	     wall_construction_type     = '1',
	     occupation_type            = '1',
	     primary_heating_type       = '1',
	     secondary_heating_type     = '2',
	     water_heating_type         = '1',
	     cooking_type               = '1',
	     depth_loft_insulation      = "10%",
	     number_open_fireplaces     = "50%",
	     double_glazing             = "100%",
	     num_occupants              = 10,
	     annual_gas_kwh             = 124.456,
	     annual_gas_estimated       = True,
	     annual_gas_start_date      = '02/02/2017',
	     annual_gas_end_date        = '03/02/2017',
	     annual_elec_kwh            = 123.456,
	     annual_elec_estimated      = True,
	     annual_elec_start_date     = '04/02/2017',
	     annual_elec_end_date       = '05/02/2017',
	     annual_solid_spend         = 123.456,
	     renewable_contribution_kwh = 123.456,
	     faults_identified          = 'faults_identified',
	     recommendations            = 'recommendations',
	   ), follow_redirects=True)
    assert b'Survey result submitted successfully' in rv.data
    logout(client)
    with app.app_context():
        result = Results.query.filter(Results.lead_surveyor=='test_lead_surveyor').first()
	assert result.survey                     == Surveys.query.get(1)
	assert result.lead_surveyor              == 'test_lead_surveyor'
	assert result.assistant_surveyor         == 'assistant_surveyor'
	assert result.householders_name          == 'householders_name'
	assert result.address_line               == 'address_line'
	assert result.survey_date                == datetime.date(2017, 2, 1)
	assert result.external_temperature       == 123.456
	assert result.camera_kit_number          == 'Camera kit 17'
	assert result.loaned_cheese_box          == True
	assert result.cheese_box_number          == 'Box 42'
	assert result.year_of_construction       == 1970
	assert result.building_type              == BuildingTypes.query.get(1)
	assert result.wall_construction_type     == WallConstructionTypes.query.get(1)
	assert result.occupation_type            == OccupationTypes.query.get(1)
	assert result.primary_heating_type       == SpaceHeatingTypes.query.get(1)
	assert result.secondary_heating_type     == SpaceHeatingTypes.query.get(2)
	assert result.water_heating_type         == WaterHeatingTypes.query.get(1)
	assert result.cooking_type               == CookingTypes.query.get(1)
	assert result.depth_loft_insulation      == '10%'
	assert result.number_open_fireplaces     == '50%'
	assert result.double_glazing             == '100%'
	assert result.num_occupants              == 10
	assert result.annual_gas_kwh             == 124.456
	assert result.annual_gas_estimated       == True
	assert result.annual_gas_start_date      == datetime.date(2017, 2, 2)
	assert result.annual_gas_end_date        == datetime.date(2017, 2, 3)
	assert result.annual_elec_kwh            == 123.456
	assert result.annual_elec_estimated      == True
	assert result.annual_elec_start_date     == datetime.date(2017, 2, 4)
	assert result.annual_elec_end_date       == datetime.date(2017, 2, 5)
	assert result.annual_solid_spend         == 123.456
	assert result.renewable_contribution_kwh == 123.456
	assert result.faults_identified          == 'faults_identified'
	assert result.recommendations            == 'recommendations'

ONE_MONTH_REQ_FIELDS = dict(householders_name     = 'householders_name',
                            address               = 'address',
                            satisfaction_1to5     = '5',
                            cheese_box_1to5       = '5',
                            survey_video_1to5     = '5',
                            surveyor_conduct_1to5 = '5',
                            survey_value_1to5     = '5',
                            recommend_1to5        = '5',
                            cheese_box            = 'cheese_box', )

def test_month_feedback_form_full(client, app):
    # Test the form submits with valid input data.
    data = dict(submitted_by              = 'submitted_by',
                annual_gas_kwh            = 123.456,
                annual_gas_estimated      = 'True',
                annual_gas_start_date     = '01/10/2018',
                annual_gas_end_date       = '02/10/2018',
                annual_elec_kwh           = 123.456,
                annual_elec_estimated     = 'True',
                annual_elec_start_date    = '03/10/2018',
                annual_elec_end_date      = '04/10/2018',
                annual_solid_spend        = 123.456,
                renewable_contrib_kwh     = 123.456,
                any_completed_actions     = 'True',
                completed_actions         = 'completed_actions',
                any_wellbeing_improvement = 'True',
                wellbeing_improvement     = 'wellbeing_improvement',
                any_planned_work          = 'True',
                planned_actions           = 'planned_actions',
                any_behaviour_change      = 'True',
                behaviour_temperature     = 'behaviour_temperature',
                behaviour_space           = 'behaviour_space',
                behaviour_changes         = 'behaviour_changes',
                feedback                  = 'feedback', )
    data.update(ONE_MONTH_REQ_FIELDS)
    rv = client.post('/one-month-feedback', data=data, follow_redirects=True)
    assert b'Your one-month feedback was submitted successfully' in rv.data
    with app.app_context():
        feedback = MonthFeedback.query.filter(MonthFeedback.householders_name=='householders_name').first()
        assert feedback.householders_name         == 'householders_name'
        assert feedback.address                   == 'address'
        assert feedback.satisfaction_1to5         == 5
        assert feedback.cheese_box_1to5           == 5
        assert feedback.survey_video_1to5         == 5
        assert feedback.surveyor_conduct_1to5     == 5
        assert feedback.survey_value_1to5         == 5
        assert feedback.recommend_1to5            == 5
        assert feedback.cheese_box                == 'cheese_box'
        assert feedback.annual_gas_kwh            == 123.456
        assert feedback.annual_gas_estimated      == True
        assert feedback.annual_gas_start_date     == datetime.date(2018, 10, 1)
        assert feedback.annual_gas_end_date       == datetime.date(2018, 10, 2)
        assert feedback.annual_elec_kwh           == 123.456
        assert feedback.annual_elec_estimated     == True
        assert feedback.annual_elec_start_date    == datetime.date(2018, 10, 3)
        assert feedback.annual_elec_end_date      == datetime.date(2018, 10, 4)
        assert feedback.annual_solid_spend        == 123.456
        assert feedback.renewable_contrib_kwh     == 123.456
        assert feedback.any_completed_actions     == True
        assert feedback.completed_actions         == 'completed_actions'
        assert feedback.any_wellbeing_improvement == True
        assert feedback.wellbeing_improvement     == 'wellbeing_improvement'
        assert feedback.any_planned_work          == True
        assert feedback.planned_actions           == 'planned_actions'
        assert feedback.any_behaviour_change      == True
        assert feedback.behaviour_temperature     == 'behaviour_temperature'
        assert feedback.behaviour_space           == 'behaviour_space'
        assert feedback.behaviour_changes         == 'behaviour_changes'
        assert feedback.feedback                  == 'feedback'

def test_month_feedback_form_req(client, app):
    # Only required data.
    data = dict()
    data.update(ONE_MONTH_REQ_FIELDS)
    rv = client.post('/one-month-feedback', data=data, follow_redirects=True)
    assert b'Your one-month feedback was submitted successfully' in rv.data

def test_month_feedback_form_completed_actions_requiredif(client, app):
    data = dict()
    data.update(ONE_MONTH_REQ_FIELDS)
    data['any_completed_actions'] = 'True'
    rv = client.post('/one-month-feedback', data=data, follow_redirects=True)
    assert rv.data.count(b'This field is required') == 1

def test_month_feedback_form_wellbeing_requiredif(client, app):
    data = dict()
    data.update(ONE_MONTH_REQ_FIELDS)
    data['any_wellbeing_improvement'] = 'True'
    rv = client.post('/one-month-feedback', data=data, follow_redirects=True)
    assert rv.data.count(b'This field is required') == 1

def test_month_feedback_form_planned_work_requiredif(client, app):
    data = dict()
    data.update(ONE_MONTH_REQ_FIELDS)
    data['any_planned_work'] = 'True'
    rv = client.post('/one-month-feedback', data=data, follow_redirects=True)
    assert rv.data.count(b'This field is required') == 1

def test_month_feedback_form_behaviour_requiredif(client, app):
    data = dict()
    data.update(ONE_MONTH_REQ_FIELDS)
    data['any_behaviour_change'] = 'True'
    rv = client.post('/one-month-feedback', data=data, follow_redirects=True)
    assert rv.data.count(b'This field is required') == 3

ONE_YEAR_REQ_FIELDS = dict(householders_name = 'householders_name',
                           address           = 'address', )

def test_year_feedback_form_full(client, app):
   # Test the form submits with all valid input data.
    data = dict(annual_gas_kwh            = 123.456,
                annual_gas_estimated      = 'True',
                annual_gas_start_date     = '01/09/2019',
                annual_gas_end_date       = '02/09/2019',
                annual_elec_kwh           = 123.456,
                annual_elec_estimated     = 'True',
                annual_elec_start_date    = '03/09/2019',
                annual_elec_end_date      = '04/09/2019',
                annual_solid_spend        = 123.456,
                renewable_contrib_kwh     = 123.456,
                any_completed_actions     = 'True',
                diy_work                  = 'diy_work',
                prof_work                 = 'prof_work',
                contractors_used          = 'contractors_used',
                total_spent               = 123.456,
                total_spent_diy           = 123.456,
                total_spent_local         = 123.456,
                any_planned_work          = 'True',
                planned_work              = 'planned_work',
                any_wellbeing_improvement = 'True',
                wellbeing_improvement     = 'wellbeing_improvement',
                any_behaviour_change      = 'True',
                behaviour_temperature     = 'behaviour_temperature',
                behaviour_space           = 'behaviour_space',
                behaviour_changes         = 'behaviour_changes',
                feedback                  = 'feedback', )
    data.update(ONE_YEAR_REQ_FIELDS)
    rv = client.post('/one-year-feedback', data=data, follow_redirects=True)
    assert b'Your one-year feedback was submitted successfully' in rv.data
    with app.app_context():
        feedback = YearFeedback.query.filter(YearFeedback.householders_name=='householders_name').first()
        assert feedback.householders_name         == 'householders_name'
        assert feedback.address                   == 'address'
        assert feedback.annual_gas_kwh            == 123.456
        assert feedback.annual_gas_estimated      == True
        assert feedback.annual_gas_start_date     == datetime.date(2019, 9, 1)
        assert feedback.annual_gas_end_date       == datetime.date(2019, 9, 2)
        assert feedback.annual_elec_kwh           == 123.456
        assert feedback.annual_elec_estimated     == True
        assert feedback.annual_elec_start_date    == datetime.date(2019, 9, 3)
        assert feedback.annual_elec_end_date      == datetime.date(2019, 9, 4)
        assert feedback.annual_solid_spend        == 123.456
        assert feedback.renewable_contrib_kwh     == 123.456
        assert feedback.any_completed_actions     == True
        assert feedback.diy_work                  == 'diy_work'
        assert feedback.prof_work                 == 'prof_work'
        assert feedback.contractors_used          == 'contractors_used'
        assert feedback.total_spent               == 123.456
        assert feedback.total_spent_diy           == 123.456
        assert feedback.total_spent_local         == 123.456
        assert feedback.any_planned_work          == True
        assert feedback.planned_work              == 'planned_work'
        assert feedback.any_wellbeing_improvement == True
        assert feedback.wellbeing_improvement     == 'wellbeing_improvement'
        assert feedback.any_behaviour_change      == True
        assert feedback.behaviour_temperature     == 'behaviour_temperature'
        assert feedback.behaviour_space           == 'behaviour_space'
        assert feedback.behaviour_changes         == 'behaviour_changes'
        assert feedback.feedback                  == 'feedback'

def test_year_feedback_form_req(client, app):
    # Only required fields.
    data = dict()
    data.update(ONE_YEAR_REQ_FIELDS)
    rv = client.post('/one-year-feedback', data=data, follow_redirects=True)
    assert b'Your one-year feedback was submitted successfully' in rv.data

def test_year_feedback_form_completed_actions_requiredif(client, app):
    data = dict()
    data.update(ONE_YEAR_REQ_FIELDS)
    data['any_completed_actions'] = 'True'
    rv = client.post('/one-year-feedback', data=data, follow_redirects=True)
    assert rv.data.count(b'This field is required') == 2

def test_year_feedback_form_wellbeing_requiredif(client, app):
    data = dict()
    data.update(ONE_YEAR_REQ_FIELDS)
    data['any_wellbeing_improvement'] = 'True'
    rv = client.post('/one-year-feedback', data=data, follow_redirects=True)
    assert rv.data.count(b'This field is required') == 1

def test_year_feedback_form_planned_work_requiredif(client, app):
    data = dict()
    data.update(ONE_YEAR_REQ_FIELDS)
    data['any_planned_work'] = 'True'
    rv = client.post('/one-year-feedback', data=data, follow_redirects=True)
    assert rv.data.count(b'This field is required') == 1

def test_year_feedback_form_behaviour_requiredif(client, app):
    data = dict()
    data.update(ONE_YEAR_REQ_FIELDS)
    data['any_behaviour_change'] = 'True'
    rv = client.post('/one-year-feedback', data=data, follow_redirects=True)
    assert rv.data.count(b'This field is required') == 3

# Tests the form submits with valid input data.
def test_membership_form(client, app):
    rv = client.post('/apply-for-membership', data=dict(
             registration_date           = '01/01/2018',
             name                        = 'test_name',
             address                     = 'address',
             email                       = 'email',
             telephone                   = 'telephone',
             representative_1_name       = 'representative_1_name',
             representative_1_email      = 'representative_1_email',
             representative_1_telephone  = 'representative_1_telephone',
             representative_2_name       = 'representative_2_name',
             representative_2_email      = 'representative_2_email',
             representative_2_telephone  = 'representative_2_telephone',
           ), follow_redirects=True)
    # Check the form submitted with a message.
    assert b'Your membership application was submitted successfully' in rv.data
    # Check the database was populated.
    with app.app_context():
        member = Member.query.filter(Member.name=='test_name').first()
        assert member.address                     == 'address'
        assert member.email                       == 'email'
        assert member.telephone                   == 'telephone'
        assert member.representative_1_name       == 'representative_1_name'
        assert member.representative_1_email      == 'representative_1_email'
        assert member.representative_1_telephone  == 'representative_1_telephone'
        assert member.representative_2_name       == 'representative_2_name'
        assert member.representative_2_email      == 'representative_2_email'
        assert member.representative_2_telephone  == 'representative_2_telephone'

def test_upload_thermal_image_full(client, app):
    rv = admin_login(client)
    rv = client.post('/upload-thermal-image', content_type='multipart/form-data', data=dict(
          image_file           = (BytesIO(b'blah'), 'img.jpg'),
          description          = 'description',
          building_type        = '1',
          year_of_construction = 1970,
          keywords             = 'keywords',
        ), follow_redirects=True)
    logout(client)
    assert b'The thermal image has been submitted successfully' in rv.data
    with app.app_context():
        image = ThermalImage.query.limit(1).all()[0]
        assert image.description          == 'description'
        assert image.keywords             == 'keywords'
        assert image.building_type        == BuildingTypes.query.get(1)
        assert image.year_of_construction == 1970
        assert image.filename             != None

def test_upload_thermal_image_required(client, app):
    # building_type is optional.
    rv = admin_login(client)
    rv = client.post('/upload-thermal-image', content_type='multipart/form-data', data=dict(
          image_file           = (BytesIO(b'blah'), 'img.jpg'),
          description          = 'description',
          year_of_construction = 1970,
          keywords             = 'keywords',
        ), follow_redirects=True)
    logout(client)
    assert b'The thermal image has been submitted successfully' in rv.data
    with app.app_context():
        image = ThermalImage.query.limit(1).all()[0]
        assert image.description          == 'description'
        assert image.keywords             == 'keywords'
        assert image.year_of_construction == 1970
        assert image.filename             != None

