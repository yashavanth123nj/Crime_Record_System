from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from sqlalchemy import UniqueConstraint

# User model with role-based access control
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='admin')  # admin, officer, analyst
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    profile_image_url = db.Column(db.String(255), nullable=True)
    active = db.Column(db.Boolean, default=True)
    
    # UserMixin property override
    @property
    def is_active(self):
        return self.active
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_cases = db.relationship('Case', backref='assigned_officer', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_officer(self):
        return self.role == 'officer' or self.role == 'admin'
    
    def is_analyst(self):
        return self.role == 'analyst' or self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.email or self.id}>'

# OAuth model for Replit authentication
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

# Police Station model
class PoliceStation(db.Model):
    __tablename__ = 'police_stations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    officers = db.relationship('PoliceOfficer', backref='station', lazy='dynamic')
    
    def __repr__(self):
        return f'<PoliceStation {self.name}>'

# Police Officer model
class PoliceOfficer(db.Model):
    __tablename__ = 'police_officers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.String(50), nullable=False)
    badge_number = db.Column(db.String(50), unique=True)
    contact = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    station_id = db.Column(db.Integer, db.ForeignKey('police_stations.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (cases will be handled through User)
    user = db.relationship('User', backref='officer_profile')
    
    def __repr__(self):
        return f'<PoliceOfficer {self.name}>'

# Criminal model
class Criminal(db.Model):
    __tablename__ = 'criminals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    alias = db.Column(db.String(100))
    gender = db.Column(db.String(10))
    date_of_birth = db.Column(db.Date)
    address = db.Column(db.String(255))
    nationality = db.Column(db.String(50))
    identification_marks = db.Column(db.String(255))
    photo_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    crimes = db.relationship('CriminalCrime', backref='criminal', lazy='dynamic')
    
    def __repr__(self):
        return f'<Criminal {self.name}>'

# Crime model
class Crime(db.Model):
    __tablename__ = 'crimes'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time)
    location = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    status = db.Column(db.String(20), default='reported')  # reported, investigating, solved, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    criminals = db.relationship('CriminalCrime', backref='crime', lazy='dynamic')
    victims = db.relationship('Victim', backref='crime', lazy='dynamic')
    witnesses = db.relationship('Witness', backref='crime', lazy='dynamic')
    evidence = db.relationship('Evidence', backref='crime', lazy='dynamic')
    cases = db.relationship('Case', backref='crime', lazy='dynamic')
    
    def __repr__(self):
        return f'<Crime {self.id}: {self.type}>'

# Many-to-many relationship between Criminals and Crimes
class CriminalCrime(db.Model):
    __tablename__ = 'criminal_crime'
    
    id = db.Column(db.Integer, primary_key=True)
    criminal_id = db.Column(db.Integer, db.ForeignKey('criminals.id'), nullable=False)
    crime_id = db.Column(db.Integer, db.ForeignKey('crimes.id'), nullable=False)
    role = db.Column(db.String(50))  # e.g., 'suspect', 'accomplice', 'convicted'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Case model
class Case(db.Model):
    __tablename__ = 'cases'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')  # open, investigating, closed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    crime_id = db.Column(db.Integer, db.ForeignKey('crimes.id'))
    officer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    notes = db.relationship('CaseNote', backref='case', lazy='dynamic')
    
    def __repr__(self):
        return f'<Case {self.id}: {self.title}>'

# Case Notes model
class CaseNote(db.Model):
    __tablename__ = 'case_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='case_notes')
    
    def __repr__(self):
        return f'<CaseNote {self.id}>'

# Victim model
class Victim(db.Model):
    __tablename__ = 'victims'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    contact = db.Column(db.String(50))
    address = db.Column(db.String(255))
    statement = db.Column(db.Text)
    crime_id = db.Column(db.Integer, db.ForeignKey('crimes.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Victim {self.name}>'

# Witness model
class Witness(db.Model):
    __tablename__ = 'witnesses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(50))
    address = db.Column(db.String(255))
    statement = db.Column(db.Text)
    relation_to_victim = db.Column(db.String(100))
    crime_id = db.Column(db.Integer, db.ForeignKey('crimes.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Witness {self.name}>'

# Evidence model
class Evidence(db.Model):
    __tablename__ = 'evidence'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))
    description = db.Column(db.Text)
    location_found = db.Column(db.String(255))
    collection_date = db.Column(db.DateTime)
    custodian = db.Column(db.String(100))
    storage_location = db.Column(db.String(255))
    crime_id = db.Column(db.Integer, db.ForeignKey('crimes.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Evidence {self.name}>'
