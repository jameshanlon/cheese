import csv
import sys
from datetime import datetime, timedelta
from cheese.init_app import app, init_app, db
init_app(app)
from cheese.models import Surveys, YearFeedback

# Add skeleton Surveys records for each one-year feedback without one.
year_feedback = YearFeedback.query.all()
for x in year_feedback:
    if x.survey == None:
        request_date = (x.date - timedelta(app.config['ONE_YEAR_FOLLOW_UP_DAYS'])).date()
        s = Surveys(name=x.householders_name,
                    address_line=x.address,
                    survey_request_date=request_date,
                    notes='This survey record was created automatically from a one-year response. The request date is estimated.',
                    year_feedback=[x])
        x.survey=s
        db.session.add(s)
        print 'Added Surveys record for '+x.householders_name
db.session.commit()
