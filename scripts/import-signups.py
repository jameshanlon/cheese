import csv
import sys
from datetime import datetime
from cheese.init_app import app, init_app, db
init_app(app)
from cheese.models import Surveys

COL_NAME     = 0
COL_ADDRESS  = 1
COL_POSTCODE = 2
COL_WARD     = 3
COL_EMAIL    = 4
COL_PHONE    = 5
COL_EVENT    = 6
COL_DATE     = 7
COL_NOTES    = 8

f = open(sys.argv[1], 'r')
reader = csv.reader(f)
for row in reader:
  date = None
  if row[COL_DATE]:
    date = datetime.strptime(row[COL_DATE], '%d-%b-%Y')
  s = Surveys(name=row[COL_NAME],
              address_line=row[COL_ADDRESS],
              postcode=row[COL_POSTCODE],
              ward=row[COL_WARD],
              email=row[COL_EMAIL],
              telephone=row[COL_PHONE],
              signed_up_via='Signup form at '+row[COL_EVENT],
              referral=row[COL_EVENT],
              survey_request_date=date,
              notes=row[COL_NOTES])
  db.session.add(s)
db.session.commit()
f.close()
