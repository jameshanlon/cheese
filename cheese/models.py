import datetime
from flask_user import SQLAlchemyAdapter, UserManager, UserMixin
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate(compare_type=True)

class Wards(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    def __repr__(self):
        return self.name


class BuildingTypes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    def __repr__(self):
        return self.name


class WallConstructionTypes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    def __repr__(self):
        return self.name


class OccupationTypes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    def __repr__(self):
        return self.name


class SpaceHeatingTypes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    def __repr__(self):
        return self.name


class WaterHeatingTypes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    def __repr__(self):
        return self.name


class CookingTypes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    def __repr__(self):
        return self.name


class SurveyLeadStatuses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    def __repr__(self):
        return self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email                = db.Column(db.String(255), nullable=False, unique=True)
    password             = db.Column(db.String(255), nullable=False, server_default='')
    reset_password_token = db.Column(db.String(100), nullable=False, server_default='')
    confirmed_at         = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    active               = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
    first_name           = db.Column(db.String(100), nullable=False, server_default='')
    last_name            = db.Column(db.String(100), nullable=False, server_default='')
    # Role relationship.
    roles                = db.relationship('Role', secondary='user_roles',
                                           backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        if self.first_name != '' or self.last_name != '':
            return self.first_name+' '+self.last_name
        else:
            return self.email


class UserInvitation(db.Model):
    __tablename__ = 'user_invite'
    id = db.Column(db.Integer, primary_key=True)
    email              = db.Column(db.String(255), nullable=False)
    invited_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    token              = db.Column(db.String(100), nullable=False, server_default='')

# Setup Flask-User
db_adapter = SQLAlchemyAdapter(db, User, UserInvitationClass=UserInvitation)
user_manager = UserManager()

class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __repr__(self):
        return self.name


class UserRoles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_date            = db.Column(db.Date,
                                            default=datetime.datetime.utcnow)
    registration_date           = db.Column(db.Date)
    name                        = db.Column(db.String(250))
    address                     = db.Column(db.String(500))
    email                       = db.Column(db.String(100))
    telephone                   = db.Column(db.String(20))
    representative_1_name       = db.Column(db.String(100))
    representative_1_email      = db.Column(db.String(100))
    representative_1_telephone  = db.Column(db.String(100))
    representative_2_name       = db.Column(db.String(100))
    representative_2_email      = db.Column(db.String(100))
    representative_2_telephone  = db.Column(db.String(100))
    notes                       = db.Column(db.Text)


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name                = db.Column(db.String(200))
    asset_number        = db.Column(db.Integer, unique=True)
    serial_number       = db.Column(db.String(50), unique=True)
    date_of_purchase    = db.Column(db.Date)
    value               = db.Column(db.Float)
    sim_iccid           = db.Column(db.String(25), unique=True)
    imei                = db.Column(db.String(25), unique=True)
    phone_number        = db.Column(db.String(20), unique=True)
    icloud_username     = db.Column(db.String(25))
    icloud_password     = db.Column(db.String(25))
    credit_amount       = db.Column(db.Float)
    credit_date         = db.Column(db.Date)
    notes               = db.Column(db.Text)
    # Kit
    kit_id = db.Column(db.Integer, db.ForeignKey('kits.id'))
    kit    = db.relationship('Kits')

    def __repr__(self):
        return self.name+' (#'+str(self.asset_number)+')'


class Kits(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(200))
    notes        = db.Column(db.Text())
    # Inventory
    inventory  = db.relationship('Inventory')

    def __repr__(self):
        if self.name:
            return self.name
        return 'Unnamed kit '+str(self.id)


class Surveys(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name                      = db.Column(db.String(100))
    address_line              = db.Column(db.String(100))
    postcode                  = db.Column(db.String(10))
    ward_id                   = db.Column(db.Integer, db.ForeignKey('wards.id'))
    ward                      = db.relationship('Wards')
    email                     = db.Column(db.String(100))
    telephone                 = db.Column(db.String(20))
    mobile                    = db.Column(db.String(20))
    reference                 = db.Column(db.String(8))
    lead_status_id            = db.Column(db.Integer, db.ForeignKey('survey_lead_statuses.id'))
    lead_status               = db.relationship('SurveyLeadStatuses')
    survey_request_date       = db.Column(db.Date,
                                          default=datetime.datetime.utcnow)
    phase                     = db.Column(db.Integer, default=-1)
    photo_release             = db.Column(db.Boolean, default=False)
    building_type_id          = db.Column(db.Integer, db.ForeignKey('building_types.id'))
    building_type             = db.relationship('BuildingTypes')
    num_main_rooms            = db.Column(db.Integer)
    can_heat_comfortably      = db.Column(db.Boolean, default=False) # Deprecated
    expected_benefit          = db.Column(db.Text)
    signed_up_via             = db.Column(db.String(250))
    referral                  = db.Column(db.String(250))
    availability              = db.Column(db.Text)
    free_survey_consideration = db.Column(db.Boolean, default=False)
    fee                       = db.Column(db.Float)
    fee_paid                  = db.Column(db.Boolean, default=False)
    fee_paid_date             = db.Column(db.Date)
    survey_date               = db.Column(db.DateTime)
    survey_complete           = db.Column(db.Boolean, default=False)
    followed_up               = db.Column(db.Boolean, default=False)
    box_collected             = db.Column(db.Boolean, default=False)
    special_considerations    = db.Column(db.Text)
    notes                     = db.Column(db.Text)
    result                    = db.relationship('Results')
    pre_details               = db.relationship('PreSurveyDetails')
    post_details              = db.relationship('PostSurveyDetails')
    month_feedback            = db.relationship('MonthFeedback')
    year_feedback             = db.relationship('YearFeedback')

    def __repr__(self):
        if self.name and self.address_line:
            return self.name+', '+self.address_line
        elif self.name:
            return self.name
        elif self.address_line:
            return self.address_line
        return 'Survey '+str(self.id)


class Results(db.Model):
    # This table has been deprecated. Details of the home are now provided by
    # the householder in HomeDetails and details of the survey are provided
    # by the ET in SurveyDetails.
    id = db.Column(db.Integer, primary_key=True)
    date                       = db.Column(db.DateTime,
                                           default=datetime.datetime.utcnow)
    lead_surveyor              = db.Column(db.String(50))
    assistant_surveyor         = db.Column(db.String(50))
    householders_name          = db.Column(db.String(50))
    address_line               = db.Column(db.String(100))
    survey_date                = db.Column(db.Date)
    external_temperature       = db.Column(db.Float)
    camera_kit_number          = db.Column(db.String(25))
    loaned_cheese_box          = db.Column(db.Boolean, default=False)
    cheese_box_number          = db.Column(db.String(25))
    building_type_id           = db.Column(db.Integer, db.ForeignKey('building_types.id'))
    building_type              = db.relationship('BuildingTypes')
    year_of_construction       = db.Column(db.Integer)
    wall_construction_type_id  = db.Column(db.Integer, db.ForeignKey('wall_construction_types.id'))
    wall_construction_type     = db.relationship('WallConstructionTypes')
    occupation_type_id         = db.Column(db.Integer, db.ForeignKey('occupation_types.id'))
    occupation_type            = db.relationship('OccupationTypes')
    primary_heating_type_id    = db.Column(db.Integer, db.ForeignKey('space_heating_types.id'))
    primary_heating_type       = db.relationship('SpaceHeatingTypes', foreign_keys=primary_heating_type_id)
    secondary_heating_type_id  = db.Column(db.Integer, db.ForeignKey('space_heating_types.id'))
    secondary_heating_type     = db.relationship('SpaceHeatingTypes', foreign_keys=secondary_heating_type_id)
    water_heating_type_id      = db.Column(db.Integer, db.ForeignKey('water_heating_types.id'))
    water_heating_type         = db.relationship('WaterHeatingTypes')
    cooking_type_id            = db.Column(db.Integer, db.ForeignKey('cooking_types.id'))
    cooking_type               = db.relationship('CookingTypes')
    depth_loft_insulation      = db.Column(db.String(150))
    number_open_fireplaces     = db.Column(db.String(150))
    double_glazing             = db.Column(db.String(150))
    num_occupants              = db.Column(db.Integer)
    annual_gas_kwh             = db.Column(db.Float)
    annual_gas_estimated       = db.Column(db.Boolean)
    annual_gas_start_date      = db.Column(db.Date)
    annual_gas_end_date        = db.Column(db.Date)
    annual_elec_kwh            = db.Column(db.Float)
    annual_elec_estimated      = db.Column(db.Boolean)
    annual_elec_start_date     = db.Column(db.Date)
    annual_elec_end_date       = db.Column(db.Date)
    annual_solid_spend         = db.Column(db.Float)
    renewable_contribution_kwh = db.Column(db.Float)
    faults_identified          = db.Column(db.Text)
    recommendations            = db.Column(db.Text)
    notes                      = db.Column(db.Text)
    # Survey ref
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'))
    survey    = db.relationship('Surveys')

    def __repr__(self):
        return '<Result '+str(self.id)+'>'


class PreSurveyDetails(db.Model):
    # This table is now used to record householder-supplied survey details.
    # Should be 'HomeDetails'
    id = db.Column(db.Integer, primary_key=True)
    date                       = db.Column(db.DateTime,
					   default=datetime.datetime.utcnow)
    householders_name          = db.Column(db.String(50))
    address_line               = db.Column(db.String(100))
    postcode                   = db.Column(db.String(10))
    special_considerations     = db.Column(db.Text)
    num_main_rooms             = db.Column(db.Integer)
    can_heat_comfortably       = db.Column(db.Boolean, default=False)
    expected_benefit           = db.Column(db.Text)
    year_of_construction       = db.Column(db.Integer)
    building_type_id           = db.Column(db.Integer,
					   db.ForeignKey('building_types.id'))
    building_type              = db.relationship('BuildingTypes')
    wall_construction_type_id  = db.Column(db.Integer,
					   db.ForeignKey('wall_construction_types.id'))
    wall_construction_type     = db.relationship('WallConstructionTypes')
    occupation_type_id         = db.Column(db.Integer,
					   db.ForeignKey('occupation_types.id'))
    occupation_type            = db.relationship('OccupationTypes')
    primary_heating_type_id    = db.Column(db.Integer,
					   db.ForeignKey('space_heating_types.id'))
    primary_heating_type       = db.relationship('SpaceHeatingTypes',
						 foreign_keys=primary_heating_type_id)
    secondary_heating_type_id  = db.Column(db.Integer,
					   db.ForeignKey('space_heating_types.id'))
    secondary_heating_type     = db.relationship('SpaceHeatingTypes',
						 foreign_keys=secondary_heating_type_id)
    water_heating_type_id      = db.Column(db.Integer,
					   db.ForeignKey('water_heating_types.id'))
    water_heating_type         = db.relationship('WaterHeatingTypes')
    cooking_type_id            = db.Column(db.Integer,
					   db.ForeignKey('cooking_types.id'))
    cooking_type               = db.relationship('CookingTypes')
    depth_loft_insulation      = db.Column(db.String(150))
    number_open_fireplaces     = db.Column(db.String(150))
    double_glazing             = db.Column(db.String(150))
    num_occupants              = db.Column(db.Integer)
    has_asbestos               = db.Column(db.Boolean)
    asbestos_details           = db.Column(db.Text)
    annual_gas_kwh             = db.Column(db.Float)
    annual_gas_estimated       = db.Column(db.Boolean)
    annual_gas_start_date      = db.Column(db.Date)
    annual_gas_end_date        = db.Column(db.Date)
    annual_elec_kwh            = db.Column(db.Float)
    annual_elec_estimated      = db.Column(db.Boolean)
    annual_elec_start_date     = db.Column(db.Date)
    annual_elec_end_date       = db.Column(db.Date)
    annual_solid_spend         = db.Column(db.Float)
    renewable_contribution_kwh = db.Column(db.Float)
    notes                      = db.Column(db.Text)
    # Survey ref
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'))
    survey    = db.relationship('Surveys')

    def __repr__(self):
	return '<PreSurveyDetails '+str(self.id)+'>'


class PostSurveyDetails(db.Model):
    # This table records surveyor-recorded details of the survey.
    id = db.Column(db.Integer, primary_key=True)
    date                       = db.Column(db.DateTime,
					   default=datetime.datetime.utcnow)
    lead_surveyor              = db.Column(db.String(50))
    assistant_surveyor         = db.Column(db.String(50))
    survey_date                = db.Column(db.Date)
    camera_kit_number          = db.Column(db.String(25))
    external_temperature       = db.Column(db.Float)
    faults_identified          = db.Column(db.Text)
    recommendations            = db.Column(db.Text)
    notes                      = db.Column(db.Text)
    # Survey ref
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'))
    survey    = db.relationship('Surveys')

    def __repr__(self):
	return '<PostSurveyDetails '+str(self.id)+'>'

class MonthFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date                      = db.Column(db.DateTime,
                                          default=datetime.datetime.utcnow)
    submitted_by              = db.Column(db.String(50))
    householders_name         = db.Column(db.String(50))
    address                   = db.Column(db.String(100))
    annual_gas_kwh            = db.Column(db.Float)
    annual_gas_estimated      = db.Column(db.Boolean)
    annual_gas_start_date     = db.Column(db.Date)
    annual_gas_end_date       = db.Column(db.Date)
    annual_elec_kwh           = db.Column(db.Float)
    annual_elec_estimated     = db.Column(db.Boolean)
    annual_elec_start_date    = db.Column(db.Date)
    annual_elec_end_date      = db.Column(db.Date)
    annual_solid_spend        = db.Column(db.Float)
    renewable_contrib_kwh     = db.Column(db.Float)
    any_completed_actions     = db.Column(db.Boolean)
    completed_actions         = db.Column(db.Text)
    any_wellbeing_improvement = db.Column(db.Boolean)
    wellbeing_improvement     = db.Column(db.Text)
    any_planned_work          = db.Column(db.Boolean)
    planned_actions           = db.Column(db.Text)
    cheese_box                = db.Column(db.Text)
    any_behaviour_change      = db.Column(db.Boolean)
    behaviour_temperature     = db.Column(db.Text)
    behaviour_space           = db.Column(db.Text)
    behaviour_changes         = db.Column(db.Text)
    satisfaction_1to5         = db.Column(db.Integer)
    cheese_box_1to5           = db.Column(db.Integer)
    survey_video_1to5         = db.Column(db.Integer)
    surveyor_conduct_1to5     = db.Column(db.Integer)
    survey_value_1to5         = db.Column(db.Integer)
    recommend_1to5            = db.Column(db.Integer)
    feedback                  = db.Column(db.Text)
    notes                     = db.Column(db.Text)
    # Survey ref
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'))
    survey    = db.relationship('Surveys')

    def __repr__(self):
        return '<Month feedback '+str(self.id)+'>'


class YearFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date                      = db.Column(db.DateTime,
                                          default=datetime.datetime.utcnow)
    submitted_by              = db.Column(db.String(50))
    householders_name         = db.Column(db.String(50))
    address                   = db.Column(db.String(100))
    annual_gas_kwh            = db.Column(db.Float)
    annual_gas_estimated      = db.Column(db.Boolean)
    annual_gas_start_date     = db.Column(db.Date)
    annual_gas_end_date       = db.Column(db.Date)
    annual_elec_kwh           = db.Column(db.Float)
    annual_elec_estimated     = db.Column(db.Boolean)
    annual_elec_start_date    = db.Column(db.Date)
    annual_elec_end_date      = db.Column(db.Date)
    annual_solid_spend        = db.Column(db.Float)
    renewable_contrib_kwh     = db.Column(db.Float)
    any_completed_actions     = db.Column(db.Boolean)
    diy_work                  = db.Column(db.Text)
    prof_work                 = db.Column(db.Text)
    contractors_used          = db.Column(db.Text)
    total_spent               = db.Column(db.Float)
    total_spent_diy           = db.Column(db.Float)
    total_spent_local         = db.Column(db.Float)
    non_homeowner_work        = db.Column(db.Text)
    any_planned_work          = db.Column(db.Boolean)
    planned_work              = db.Column(db.Text)
    any_wellbeing_improvement = db.Column(db.Boolean)
    wellbeing_improvement     = db.Column(db.Text)
    any_behaviour_change      = db.Column(db.Boolean)
    behaviour_temperature     = db.Column(db.Text)
    behaviour_space           = db.Column(db.Text)
    behaviour_changes         = db.Column(db.Text)
    feedback                  = db.Column(db.Text)
    notes                     = db.Column(db.Text)
    # Survey ref
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'))
    survey    = db.relationship('Surveys')

    def __repr__(self):
        return '<Year feedback '+str(self.id)+'>'


class ThermalImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename             = db.Column(db.Unicode(100))
    description          = db.Column(db.UnicodeText)
    building_type_id     = db.Column(db.Integer, db.ForeignKey('building_types.id'))
    building_type        = db.relationship('BuildingTypes')
    year_of_construction = db.Column(db.Integer)
    keywords             = db.Column(db.String(150))
    submitted_by         = db.Column(db.Unicode(50)) # To remove.
    date                 = db.Column(db.DateTime,
                                     default=datetime.datetime.now)
    user_id              = db.Column(db.Integer, db.ForeignKey('user.id'))
    user                 = db.relationship('User')

    def __repr__(self):
        return '<Thermal image '+self.filename+'>'
