from cheese.factory import create_app
app=create_app({})
from cheese.models import Surveys, Results, BuildingTypes, WallConstructionTypes, CookingTypes, OccupationTypes, SpaceHeatingTypes, CookingTypes

survey_ids = [342, 426, 417, 440, 446, 461, 442, 473, 471, 476, 477, 482]

with app.app_context():
    for survey_id in survey_ids:
        survey = Surveys.query.get(survey_id)
        results = Results.query.filter(Results.survey_id==survey.id).all()
        if results == None:
            print 'No result for survey {}'.format(survey.id)
            continue
        elif len(results) > 1:
            print 'Multiple results for survey {}'.format(survey.id)
            continue
        result = results[0]
        print '='*50
        print 'SURVEY {}'.format(survey.id)
        print '='*50
        data = []
        data.append(('Survey date',               result.date))
        data.append(('Householder\'s name',       result.householders_name))
        data.append(('Lead surveyor',             result.lead_surveyor))
        data.append(('Assistant surveyor',        result.assistant_surveyor))
        data.append(('Building type',             result.building_type.name if result.building_type else 'Unspecified'))
        data.append(('Occupation type',           result.occupation_type.name if result.occupation_type else 'Unspecified'))
        data.append(('Number of occupants',       result.num_occupants))
        data.append(('External temperature',      result.external_temperature))
        data.append(('Year of construction',      result.year_of_construction))
        data.append(('Wall construction type',    result.wall_construction_type.name if result.wall_construction_type else 'Unspecified'))
        data.append(('Primary heating type',      result.primary_heating_type.name if result.primary_heating_type else 'Unspecified'))
        data.append(('Secondary heating type',    result.secondary_heating_type.name if result.secondary_heating_type else 'Unspecified'))
        data.append(('Water heating type',        result.water_heating_type.name if result.water_heating_type else 'Unspecified'))
        data.append(('Cooking type',              result.cooking_type.name if result.cooking_type else 'Unspecified'))
        data.append(('Depth of loft insulation',  result.depth_loft_insulation))
        data.append(('Number of open fireplaces', result.number_open_fireplaces))
        data.append(('Double glazing',            result.double_glazing))
        for (name, value) in data:
            print '{:<30} {}'.format(name, value)
        print
        print 'Faults:'
        print result.faults_identified.encode('utf-8')
        print
        print 'Recommendations:'
        print result.recommendations.encode('utf-8')
        print
