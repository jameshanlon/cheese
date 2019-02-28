from cheese.factory import create_app
app=create_app({})
from cheese.models import Surveys
with app.app_context():
  for x in Surveys.query.filter(Surveys.phase==4).all():
    print '{} {} {}'.format(x.id, x.survey_request_date, x.name)
  print len(Surveys.query.filter(Surveys.phase==4).all())

