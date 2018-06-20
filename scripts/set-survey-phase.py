import sys
import datetime
from cheese.factory import create_app
from cheese.models import db, Surveys
from cheese.settings import PHASE_START_DATES

config=dict()
app = create_app(config)

with app.app_context():
    for phase, start_date in enumerate(PHASE_START_DATES):
        end_date = start_date + datetime.timedelta(365.25)
        query = Surveys.query;
        query = query.filter(Surveys.survey_request_date >= start_date)
        query = query.filter(Surveys.survey_request_date < end_date)
        for survey in query.all():
            survey.phase = phase
            print 'Set phase {} for survey {}'.format(phase, survey.id)
    db.session.commit()
    print 'Surveys without a phase:'
    query = Surveys.query.filter(phase==-1)
    for survey in query.all():
        print '  id {} in phase {}'.format(survey.id, survey.phase)
