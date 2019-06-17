from cheese.factory import create_app
app=create_app({})
from cheese.models import Surveys, Results, BuildingTypes, WallConstructionTypes, CookingTypes, OccupationTypes, SpaceHeatingTypes, CookingTypes 

with app.app_context():
    for survey in Surveys.query.filter(Surveys.phase==4).all():
        x = Results.query.filter(Results.survey_id==survey.id).first()
        if x == None:
            print 'No result for survey {}'.format(survey.id)
            continue
        print 'SURVEY {}'.format(survey.id)
        result = []
        result.append(('Survey date',               x.date))
        result.append(('Householder\'s name',       x.householders_name))
        result.append(('Lead surveyor',             x.lead_surveyor))
        result.append(('Assistant surveyor',        x.assistant_surveyor))
        result.append(('Building type',             x.building_type.name if x.building_type else 'Unspecified'))
        result.append(('Occupation type',           x.occupation_type.name if x.occupation_type else 'Unspecified'))
        result.append(('Number of occupants',       x.num_occupants))
        result.append(('External temperature',      x.external_temperature))
        result.append(('Year of construction',      x.year_of_construction)) 
        result.append(('Wall construction type',    x.wall_construction_type.name if x.wall_construction_type else 'Unspecified')) 
        result.append(('Primary heating type',      x.primary_heating_type.name if x.primary_heating_type else 'Unspecified')) 
        result.append(('Secondary heating type',    x.secondary_heating_type.name if x.secondary_heating_type else 'Unspecified')) 
        result.append(('Water heating type',        x.water_heating_type.name if x.water_heating_type else 'Unspecified')) 
        result.append(('Cooking type',              x.cooking_type.name if x.cooking_type else 'Unspecified')) 
        result.append(('Depth of loft insulation',  x.depth_loft_insulation))
        result.append(('Number of open fireplaces', x.number_open_fireplaces)) 
        result.append(('Double glazing',            x.double_glazing)) 
        for (name, value) in result:
            print '{:<30} {}'.format(name, value)
        print
        print 'Faults:'
        print x.faults_identified.encode('utf-8')
        print
        print 'Recommendations:'
        print x.recommendations.encode('utf-8')
        print '-'*50

