import csv
import sys
from cheese.factory import create_app
from cheese.models import db, Results, BuildingTypes, WallConstructionTypes, OccupationTypes, SpaceHeatingTypes, CookingTypes, WaterHeatingTypes

app = create_app()
f = open(sys.argv[1], 'r')
reader = csv.reader(f)
for row in reader:
    print 'Result {}'.format(row)
    with app.app_context():
      result = Results.query.get(int(row[0]))
      result.building_type_id = BuildingTypes.query.filter_by(name=row[1].strip()).first().id
      result.wall_construction_type_id = WallConstructionTypes.query.filter_by(name=row[2].strip()).first().id
      result.occupation_type_id = OccupationTypes.query.filter_by(name=row[3].strip()).first().id
      result.primary_heating_type_id = int(row[4])
      result.secondary_heating_type_id = int(row[5])
      db.session.commit()
f.close()
