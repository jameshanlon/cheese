import datetime
import random
from mixer.backend.flask import mixer
from cheese.models import db, \
                          user_manager, \
                          User, \
                          Role, \
                          Surveys, \
                          Results, \
			  PreSurveyDetails, \
			  PostSurveyDetails, \
                          MonthFeedback, \
                          YearFeedback, \
                          Wards, \
                          BuildingTypes, \
                          WallConstructionTypes, \
                          OccupationTypes, \
                          SpaceHeatingTypes, \
                          WaterHeatingTypes, \
                          CookingTypes, \
                          SurveyLeadStatuses
from cheese.settings import PHASE_START_DATES, \
			    NUM_PHASES

def create_enum_values(db, cls, values):
    for x in values:
	value = cls()
	value.name = x
	db.session.add(value)

def resetdb():
    "Create a test database"
    names                   = ['Sue', 'Dave', 'Mike', 'Brian', 'Roz', 'Jeremy', 'Jamie', 'Maddy']
    wards                   = ['Easton', 'Lawrence Hill', 'Clifton', 'Kingsdown']
    lead_statuses           = ['Successful', 'Possible', 'Dead']
    building_types          = ['Flat', 'Terrace', 'Detached', 'Unknown']
    wall_construction_types = ['Brick', 'Stone', 'Timber', 'Unknown']
    occupation_types        = ['Rented', 'Owner', 'Unknown']
    space_heating_types     = ['Central heating', 'Gas fire', 'Electric heaters', 'Unknown']
    water_heating_types     = ['Electricity', 'Gas', 'Solar', 'Unknown']
    cooking_types           = ['Electricity', 'Gas', 'Other', 'Unknown']
    db.drop_all()
    db.create_all()
    admin_role = Role(name='admin')
    db.session.add(admin_role)
    db.session.add(Role(name='manager'))
    db.session.add(Role(name='surveyor'))
    admin_user = User(email='admin@cheeseproject.co.uk',
                      active=True,
                      password=user_manager.hash_password('admin'))
    admin_user.roles.append(admin_role)
    db.session.add(admin_user)
    # Create enum tables.
    create_enum_values(db, Wards,                 wards)
    create_enum_values(db, SurveyLeadStatuses,    lead_statuses)
    create_enum_values(db, BuildingTypes,         building_types)
    create_enum_values(db, WallConstructionTypes, wall_construction_types)
    create_enum_values(db, OccupationTypes,       occupation_types)
    create_enum_values(db, SpaceHeatingTypes,     space_heating_types)
    create_enum_values(db, WaterHeatingTypes,     water_heating_types)
    create_enum_values(db, CookingTypes,          cooking_types)
    db.session.commit()
    # Generate some random entries.
    def get_random_name():
        return random.choice(names)
    def get_random_ward():
        return random.choice(wards)
    def get_random_box_number():
        return random.randrange(100)
    def get_random_date():
        start = PHASE_START_DATES[0]
        end = PHASE_START_DATES[-1]
        delta = end - start
        return start + datetime.timedelta(random.randrange(delta.days))
    def get_random_phase():
        return random.randint(1, NUM_PHASES)
    mixer.cycle(10).blend(User)
    mixer.cycle(50).blend(Surveys,
                          name=mixer.RANDOM,
                          ward=mixer.RANDOM,
                          free_survey_consideration=mixer.RANDOM,
                          lead_status=mixer.SELECT,
                          survey_request_date=get_random_date,
                          phase=get_random_phase,
                          survey_date=get_random_date,
                          address_line=mixer.RANDOM,
                          availability=mixer.RANDOM,
                          expected_benefit=mixer.RANDOM,
                          box_collected=mixer.RANDOM,
                          notes=mixer.RANDOM)
    # This table is now deprecated for phase 5 and onwards.
    mixer.cycle(50).blend(Results,
                          survey=mixer.SELECT,
                          survey_date=get_random_date,
                          lead_surveyor=get_random_name,
                          assistant_surveyor=get_random_name,
                          cheese_box_number=get_random_box_number,
                          faults_identified=mixer.RANDOM,
                          recommendations=mixer.RANDOM,
                          notes=mixer.RANDOM)
    mixer.cycle(50).blend(PreSurveyDetails,
			  survey=mixer.SELECT,
			  householder_name=get_random_name,
			  postcode=mixer.RANDOM,
			  building_type=mixer.SELECT,
			  year_of_construction=mixer.RANDOM,
			  wall_construction_type=mixer.SELECT,
			  occupation_type=mixer.SELECT,
			  primary_heating_type=mixer.SELECT,
			  secondary_heating_type=mixer.SELECT,
			  water_heating_type=mixer.SELECT,
			  cooking_type=mixer.SELECT,
			  depth_loft_insulation=mixer.RANDOM,
			  number_open_fireplaces=mixer.RANDOM,
			  double_glazing=mixer.RANDOM,
                          has_asbestos=mixer.RANDOM,
                          asbestos_details=mixer.RANDOM,
			  num_occupants=mixer.RANDOM,
			  notes=mixer.RANDOM)
    mixer.cycle(50).blend(PostSurveyDetails,
			  survey=mixer.SELECT,
			  lead_surveyor=get_random_name,
			  assistant_surveyor=get_random_name,
			  survey_date=get_random_date,
			  camera_kit_number=mixer.RANDOM,
			  external_temperature=mixer.RANDOM,
			  faults_identified=mixer.RANDOM,
			  recommendations=mixer.RANDOM,
			  notes=mixer.RANDOM)
    mixer.cycle(50).blend(MonthFeedback,
                          survey=mixer.SELECT,
                          completed_actions=mixer.RANDOM,
                          planned_actions=mixer.RANDOM,
                          cheese_box=mixer.RANDOM,
                          feedback=mixer.RANDOM,
                          notes=mixer.RANDOM)
    mixer.cycle(20).blend(YearFeedback,
                          householders_name=mixer.RANDOM,
                          survey=mixer.SELECT,
                          diy_work=mixer.RANDOM,
                          prof_work=mixer.RANDOM,
                          contractors_used=mixer.RANDOM,
                          planned_work=mixer.RANDOM,
                          wellbeing_improvement=mixer.RANDOM,
                          behaviour_changes=mixer.RANDOM,
                          feedback=mixer.RANDOM,
                          notes=mixer.RANDOM)
    # Remove duplicate references (where there should only be one).
    for s in Surveys.query.all():
      if len(s.result) > 1:
        for x in s.result[1:]:
          db.session.delete(x)
      if len(s.pre_details) > 1:
	for x in s.pre_details[1:]:
	  db.session.delete(x)
      if len(s.post_details) > 1:
	for x in s.post_details[1:]:
	  db.session.delete(x)
      if len(s.month_feedback) > 1:
        for x in s.month_feedback[1:]:
          db.session.delete(x)
      if len(s.year_feedback) > 1:
        for x in s.year_feedback[1:]:
          db.session.delete(x)
    db.session.commit()
