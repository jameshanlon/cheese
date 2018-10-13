import csv
import sys
from cheese.factory import create_app
from cheese.models import db, ThermalImage, BuildingTypes 

app = create_app()
f = open(sys.argv[1], 'r')
reader = csv.reader(f)
for row in reader:
    print 'Result {}'.format(row)
    with app.app_context():
      result = ThermalImage.query.get(int(row[0]))
      result.building_type_id = BuildingTypes.query.filter_by(name=row[1].strip()).first().id
      db.session.commit()
f.close()
