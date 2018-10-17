import csv
import sys
from cheese.factory import create_app
from cheese.models import db, Surveys, BuildingTypes, SurveyLeadStatuses, Wards

app = create_app()
f = open(sys.argv[1], 'r')
reader = csv.reader(f)
for row in reader:
    print 'Result {}'.format(row)
    with app.app_context():
      result = Surveys.query.get(int(row[0]))
      result.ward_id = Wards.query.filter_by(name=row[1].strip()).first().id
      #result.lead_status_id = SurveyLeadStatuses.query.filter_by(name=row[1].strip()).first().id
      #result.building_type_id = BuildingTypes.query.filter_by(name=row[2].strip()).first().id
      db.session.commit()
f.close()
