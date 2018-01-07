import datetime
from flask_user import SQLAlchemyAdapter, UserManager, UserMixin
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from cheese.definitions import *

db = SQLAlchemy()
migrate = Migrate(compare_type=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email                = db.Column(db.String(255), nullable=False, unique=True)
    password             = db.Column(db.String(255), nullable=False, server_default='')
    reset_password_token = db.Column(db.String(100), nullable=False, server_default='')
    confirmed_at         = db.Column(db.DateTime(), default=datetime.datetime.now().date())
    active               = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
    first_name           = db.Column(db.String(100), nullable=False, server_default='')
    last_name            = db.Column(db.String(100), nullable=False, server_default='')
    # Role relationship.
    roles                = db.relationship('Role', secondary='user_roles',
                                           backref=db.backref('users', lazy='dynamic'))


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
    credit_date         = db.Column(db.Date())
    notes               = db.Column(db.Text())
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
    ward                      = db.Column(db.String(50))
    email                     = db.Column(db.String(100))
    telephone                 = db.Column(db.String(20))
    mobile                    = db.Column(db.String(20))
    reference                 = db.Column(db.String(8))
    lead_status               = db.Column(db.Enum(*SURVEY_LEAD_STATUSES))
    survey_request_date       = db.Column(db.Date,
                                  default=datetime.datetime.now().date())
    building_type             = db.Column(db.Enum(*BUILDING_TYPES))
    num_main_rooms            = db.Column(db.Integer)
    can_heat_comfortably      = db.Column(db.Boolean, default=False)
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
    notes                     = db.Column(db.Text)
    result                    = db.relationship('Results')
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
    id = db.Column(db.Integer, primary_key=True)
    date                       = db.Column(db.DateTime,
                                           default=datetime.datetime.now())
    lead_surveyor              = db.Column(db.String(50))
    assistant_surveyor         = db.Column(db.String(50))
    householders_name          = db.Column(db.String(50))
    address_line               = db.Column(db.String(100))
    survey_date                = db.Column(db.Date)
    external_temperature       = db.Column(db.Float)
    loaned_cheese_box          = db.Column(db.Boolean, default=False)
    cheese_box_number          = db.Column(db.String(25))
    building_type              = db.Column(db.Enum(*BUILDING_TYPES))
    year_of_construction       = db.Column(db.Integer)
    wall_construction          = db.Column(db.Enum(*WALL_CONSTRUCTION_TYPES))
    occupation_type            = db.Column(db.Enum(*OCCUPATION_TYPES))
    primary_heating_type       = db.Column(db.String(150))
    secondary_heating_type     = db.Column(db.String(150))
    depth_loft_insulation      = db.Column(db.String(150))
    number_open_fireplaces     = db.Column(db.String(150))
    double_glazing             = db.Column(db.String(150))
    num_occupants              = db.Column(db.Integer)
    annual_gas_kwh             = db.Column(db.Float)
    annual_elec_kwh            = db.Column(db.Float)
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


class MonthFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date                  = db.Column(db.DateTime,
                                      default=datetime.datetime.now())
    submitted_by          = db.Column(db.String(50))
    householders_name     = db.Column(db.String(50))
    address               = db.Column(db.String(100))
    annual_gas_kwh        = db.Column(db.Float)
    annual_elec_kwh       = db.Column(db.Float)
    annual_solid_spend    = db.Column(db.Float)
    renewable_contrib_kwh = db.Column(db.Float)
    completed_actions     = db.Column(db.Text)
    planned_actions       = db.Column(db.Text)
    cheese_box            = db.Column(db.Text)
    feedback              = db.Column(db.Text)
    notes                 = db.Column(db.Text)
    # Survey ref
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'))
    survey    = db.relationship('Surveys')

    def __repr__(self):
        return '<Month feedback '+str(self.id)+'>'


class YearFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date                  = db.Column(db.DateTime,
                                      default=datetime.datetime.now())
    submitted_by          = db.Column(db.String(50))
    householders_name     = db.Column(db.String(50))
    address               = db.Column(db.String(100))
    annual_gas_kwh        = db.Column(db.Float)
    annual_elec_kwh       = db.Column(db.Float)
    annual_solid_spend    = db.Column(db.Float)
    renewable_contrib_kwh = db.Column(db.Float)
    diy_work              = db.Column(db.Text)
    prof_work             = db.Column(db.Text)
    contractors_used      = db.Column(db.Text)
    total_spent           = db.Column(db.Float)
    planned_work          = db.Column(db.Text)
    wellbeing_improvement = db.Column(db.Text)
    behaviour_changes     = db.Column(db.Text)
    feedback              = db.Column(db.Text)
    notes                 = db.Column(db.Text)
    # Survey ref
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'))
    survey    = db.relationship('Surveys')

    def __repr__(self):
        return '<Year feedback '+str(self.id)+'>'


class ThermalImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename             = db.Column(db.Unicode(100))
    description          = db.Column(db.UnicodeText)
    building_type        = db.Column(db.Enum(*BUILDING_TYPES))
    year_of_construction = db.Column(db.Integer)
    keywords             = db.Column(db.String(150))
    submitted_by         = db.Column(db.Unicode(50))
    date                 = db.Column(db.DateTime,
                                     default=datetime.datetime.now())

    def __repr__(self):
        return '<Thermal image '+filename+'>'
