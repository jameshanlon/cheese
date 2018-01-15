import os
import pytest
import tempfile
from cheese.factory import create_app
from cheese.models import WARDS, BUILDING_TYPES
from cheese.commands import resetdb

@pytest.fixture
def app():
    config = dict(
      FLASK_DEBUG=True,
      WTF_CSRF_ENABLED = False,
      SQLALCHEMY_DATABASE_URI = 'sqlite:///' + \
          str(tempfile.NamedTemporaryFile(suffix='.db')),
      MAIL_SUPPRESS_SEND = True, )
    app = create_app(config)
    app.testing = True
    with app.app_context():
        resetdb()
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_apply_for_survey(client, app):
    rv = client.post('/apply-for-a-survey', data=dict(
          name='name',
          address_line='address_line',
          postcode='postcode',
          ward=WARDS[0],
          email='name@domain.com',
          telephone='1234567',
          mobile='1234567',
          availability='availability',
          building_type=BUILDING_TYPES[0],
          num_main_rooms='1',
          can_heat_comfortably=True,
          expected_benefit='expected_benefit',
          referral='referral',
          free_survey_consideration=True,
          agree_to_requirements=True,
        ), follow_redirects=True)
    assert b'Your survey application has been sent!' in rv.data
