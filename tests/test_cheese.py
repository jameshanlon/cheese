import os
import pytest
import tempfile
from io import BytesIO
from cheese.factory import create_app
from cheese.models import db, User
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
             name                      = 'name',
             address_line              = 'address_line',
             postcode                  = 'postcode',
             ward                      = 1,
             email                     = 'name@domain.com',
             telephone                 = '1234567',
             mobile                    = '1234567',
             availability              = 'availability',
             building_type             = 1,
             num_main_rooms            = '1',
             can_heat_comfortably      = True,
             expected_benefit          = 'expected_benefit',
             referral                  = 'referral',
             free_survey_consideration = True,
             special_considerations    = 'special_considerations',
             agree_to_requirements     = True,
             photo_release             = True,
          ), follow_redirects=True)
    assert b'Your survey application has been sent' in rv.data

# Tests the form submits with valid input data.
def test_submit_results_form(client, app):
    rv = admin_login(client)
    rv = client.post('/submit-results', data=dict(
	     survey                     = 1,
	     lead_surveyor              = 'lead_surveyor',
	     assistant_surveyor         = 'assistant_surveyor',
	     householders_name          = 'householders_name',
	     address_line               = 'address_line',
	     survey_date                = '01/09/2018',
	     external_temperature       = 123.456,
	     loaned_cheese_box          = True,
	     cheese_box_number          = 'Box 42',
	     year_of_construction       = 1970,
	     building_type              = '1',
	     wall_construction_type     = '1',
	     occupation_type            = '1',
	     primary_heating_type       = '1',
	     secondary_heating_type     = '1',
	     water_heating_type         = '1',
	     cooking_type               = '1',
	     depth_loft_insulation      = "10%",
	     number_open_fireplaces     = "50%",
	     double_glazing             = "100%",
	     num_occupants              = 10,
	     annual_gas_kwh             = 124.456,
	     annual_gas_estimated       = True,
	     annual_gas_start_date      = '30/09/2018',
	     annual_gas_end_date        = '01/10/2019',
	     annual_elec_kwh            = 123.456,
	     annual_elec_estimated      = True,
	     annual_elec_start_date     = '30/09/2018',
	     annual_elec_end_date       = '01/10/2019',
	     annual_solid_spend         = 123.456,
	     renewable_contribution_kwh = 123.456,
	     faults_identified          = 'faults_identified',
	     recommendations            = 'recommendations',
	   ), follow_redirects=True)
    assert b'Survey result submitted successfully' in rv.data
    logout(client)

ONE_MONTH_REQ_FIELDS = dict(householders_name     = 'householders_name',
                            address               = 'address',
                            satisfaction_1to5     = '5',
                            cheese_box_1to5       = '5',
                            survey_video_1to5     = '5',
                            surveyor_conduct_1to5 = '5',
                            survey_value_1to5     = '5',
                            recommend_1to5        = '5',
                            cheese_box            = 'cheese_box', )

def test_month_feedback_form(client, app):
    # Test the form submits with valid input data.
    data = dict(submitted_by              = 'submitted_by',
                annual_gas_kwh            = 123.456,
                annual_gas_estimated      = 'True',
                annual_gas_start_date     = '30/09/2018',
                annual_gas_end_date       = '01/10/2019',
                annual_elec_kwh           = 123.456,
                annual_elec_estimated     = 'True',
                annual_elec_start_date    = '30/09/2018',
                annual_elec_end_date      = '01/10/2019',
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

def test_year_feedback_form(client, app):
   # Test the form submits with all valid input data.
    data = dict(annual_gas_kwh            = 123.456,
                annual_gas_estimated      = 'True',
                annual_gas_start_date     = '30/09/2018',
                annual_gas_end_date       = '01/10/2019',
                annual_elec_kwh           = 123.456,
                annual_elec_estimated     = 'True',
                annual_elec_start_date    = '30/09/2018',
                annual_elec_end_date      = '01/10/2019',
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
             name                        = 'name',
             address                     = 'address',
             email                       = 'email',
             telephone                   = 'telephone',
             representative_1_name       = 'representative_1_name',
             representative_1_email      = 'representative_1_email',
             representative_1_telephone  = 'representative_1_telephone',
             representative_2_name       = 'representative_2_name',
             representative_2_email      = 'representative_2_email',
             representative_2_telephone  = 'representative_2_telephone',
             notes                       = 'notes',
           ), follow_redirects=True)
    assert b'Your membership application was submitted successfully' in rv.data

def test_upload_thermal_image(client, app):
    rv = admin_login(client)
    rv = client.post('/upload-thermal-image', content_type='multipart/form-data', data=dict(
          image_file           = (BytesIO(b'blah'), 'img.jpg'),
          description          = 'description',
          year_of_construction = 1970,
          keywords             = 'keywords',
        ), follow_redirects=True)
    logout(client)
    print rv.data
    assert b'The thermal image has been submitted successfully' in rv.data
