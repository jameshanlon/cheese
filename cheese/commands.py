import datetime
import random
from mixer.backend.flask import mixer
from cheese.models import db, user_manager, User, Role, Surveys, Results, \
                          MonthFeedback, YearFeedback, Wards, \
                          BuildingTypes, WallConstructionTypes, \
                          OccupationTypes, SpaceHeatingTypes, \
                          WaterHeatingTypes, CookingTypes
from cheese.settings import PHASE_START_DATES, NUM_PHASES

def resetdb():
    "Create a test database"
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
    db.session.commit()
    # Generate some random entries.
    names = ['Jim', 'Bob', 'Sarah', 'Sue']
    wards = ['Easton', 'AWL', 'BCR', 'WOT']
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
                          lead_status=mixer.RANDOM,
                          survey_request_date=get_random_date,
                          phase=get_random_phase,
                          survey_date=get_random_date,
                          address_line=mixer.RANDOM,
                          availability=mixer.RANDOM,
                          expected_benefit=mixer.RANDOM,
                          box_collected=mixer.RANDOM,
                          notes=mixer.RANDOM)
    mixer.cycle(50).blend(Results,
                          survey=mixer.SELECT,
                          survey_date=get_random_date,
                          lead_surveyor=get_random_name,
                          assistant_surveyor=get_random_name,
                          cheese_box_number=get_random_box_number,
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
    mixer.cycle(10).blend(Wards)
    mixer.cycle(10).blend(BuildingTypes)
    mixer.cycle(10).blend(WallConstructionTypes)
    mixer.cycle(10).blend(OccupationTypes)
    mixer.cycle(10).blend(SpaceHeatingTypes)
    mixer.cycle(10).blend(WaterHeatingTypes)
    mixer.cycle(10).blend(CookingTypes)
    # Remove duplicate references (where there should only be one).
    for s in Surveys.query.all():
      if len(s.result) > 1:
        for x in s.result[1:]:
          db.session.delete(x)
      if len(s.month_feedback) > 1:
        for x in s.month_feedback[1:]:
          db.session.delete(x)
      if len(s.year_feedback) > 1:
        for x in s.year_feedback[1:]:
          db.session.delete(x)
    db.session.commit()
