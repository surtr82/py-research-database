from app import app, db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    organization = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)    

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'user_reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['user_reset_password']
        except:
            return
        return User.query.get(id)        

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)        


class Tile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    test_tile = db.Column(db.Boolean) 
    image_filename = db.Column(db.String(120))
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=True)     
    predictions = db.relationship('Prediction', backref='tile', lazy='dynamic', cascade="all, delete, delete-orphan")

    def __repr__(self):
        return '<Tile {}>'.format(self.id) 


class CertaintyScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Integer, unique=True, index=True)
    description = db.Column(db.String(120))
    sites = db.relationship('Site', backref='certainty_score', lazy='dynamic')
    
    def __repr__(self):
        return '<CertaintyScore {}>'.format(self.id) 


class CoronaConditionScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Integer, unique=True, index=True)
    description = db.Column(db.String(120))
    is_structure_recognizable = db.Column(db.Boolean, default=False)
    sites = db.relationship('Site', backref='corona_condition_score', lazy='dynamic')

    def __repr__(self):
        return '<CoronaConditionScore {}>'.format(self.id)         


class BingConditionScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Integer, unique=True, index=True)
    description = db.Column(db.String(120))
    is_structure_recognizable = db.Column(db.Boolean, default=False)
    sites = db.relationship('Site', backref='bing_condition_score', lazy='dynamic')

    def __repr__(self):
        return '<BingConditionScore {}>'.format(self.id) 
    

class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    publication_no = db.Column(db.Integer, unique=True, index=True)
    sitename = db.Column(db.String(120), index=True)
    location = db.Column(db.String(120), index=True)
    province = db.Column(db.String(120), index=True)
    district = db.Column(db.String(120), index=True)
    latitude = db.Column(db.Float, default=0)
    longitude = db.Column(db.Float, default=0)    
    est_tell_diameter = db.Column(db.String(120), default=0)
    est_lowertown_diameter = db.Column(db.String(120), default=0)
    est_tell_height = db.Column(db.String(120), default=0)
    is_registered = db.Column(db.Boolean, default=False)
    is_georeference_confirmed = db.Column(db.Boolean, default=False)
    is_georeference_outside_research_area = db.Column(db.Boolean, default=False)
    is_looted = db.Column(db.Boolean, default=False)
    certainty_score_id = db.Column(db.Integer, db.ForeignKey('certainty_score.id'))
    corona_condition_score_id = db.Column(db.Integer, db.ForeignKey('corona_condition_score.id'))
    bing_condition_score_id = db.Column(db.Integer, db.ForeignKey('bing_condition_score.id'))
    bibliography = db.Column(db.String(5000))
    tay_project = db.Column(db.String(250))    
    filename_bing_image = db.Column(db.String(120))
    filename_corona_image = db.Column(db.String(120))
    tiles = db.relationship('Tile', backref='site', lazy='dynamic')
    periods = db.relationship('SitePeriod', backref='site', lazy='dynamic', cascade="all, delete, delete-orphan")
    
    def __repr__(self):
        return '<Site {}>'.format(self.id) 


class Epoch(db.Model):
    id = db.Column(db.Integer, primary_key=True)    
    code = db.Column(db.String(20), unique=True)
    description = db.Column(db.String(120), unique=True)    

    def __repr__(self):
        return '<Epoch {}>'.format(self.id) 


class Period(db.Model):
    id = db.Column(db.Integer, primary_key=True)    
    code = db.Column(db.String(20), unique=True)
    description = db.Column(db.String(120), unique=True)
    epoch_id = db.Column(db.Integer, db.ForeignKey('epoch.id'))
    sites = db.relationship('SitePeriod', backref='period', lazy='dynamic')
    
    def __repr__(self):
        return '<Period {}>'.format(self.id)
    

class SitePeriod(db.Model):
    id = db.Column(db.Integer, primary_key=True)  
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'))    
    period_id = db.Column(db.Integer, db.ForeignKey('period.id'))
    verified = db.Column(db.Boolean, default = True)

    def __repr__(self):
        return '<SitePeriod {}>'.format(self.id)     


class RepositoryCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(120), unique=True)  
    date = db.Column(db.Date())  
    repository = db.Column(db.String(120))    
    branch = db.Column(db.String(120))    
    commit = db.Column(db.String(120), unique=True)   
    gist = db.Column(db.String(200), unique=True)  
    prediction_models = db.relationship('PredictionModel', backref='repository_code', lazy='dynamic', cascade="all, delete, delete-orphan")

    def __repr__(self):
        return '<RepositoryCode {}>'.format(self.id) 


class RepositoryData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(120), unique=True)  
    date = db.Column(db.Date())  
    repository = db.Column(db.String(120))    
    branch = db.Column(db.String(120))    
    commit = db.Column(db.String(120), unique=True)
    corona_data = db.Column(db.Boolean, default=False)
    no_images_train_tell = db.Column(db.Integer)
    no_images_train_other = db.Column(db.Integer)    
    no_images_validate_tell = db.Column(db.Integer)
    no_images_validate_other = db.Column(db.Integer)
    no_images_test_tell = db.Column(db.Integer)
    no_images_test_other = db.Column(db.Integer)
    no_images_predict_map = db.Column(db.Integer)         
    prediction_models = db.relationship('PredictionModel', backref='repository_data', lazy='dynamic', cascade="all, delete, delete-orphan")

    def __repr__(self):
        return '<RepositoryData {}>'.format(self.id) 


class PredictionModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(120), unique=True)  
    date = db.Column(db.Date()) 
    filename_validate_loss = db.Column(db.String(120))
    filename_validate_acc = db.Column(db.String(120))   
    filename_test_hist = db.Column(db.String(120))
    filename_predict_hist = db.Column(db.String(120))
    repository_code_id = db.Column(db.Integer, db.ForeignKey('repository_code.id')) 
    repository_data_id = db.Column(db.Integer, db.ForeignKey('repository_data.id')) 
    predictions = db.relationship('Prediction', backref='prediction_model', lazy='dynamic', cascade="all, delete, delete-orphan")

    def __repr__(self):
        return '<PredictionModel {}>'.format(self.id)


class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    probability = db.Column(db.Float)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)    
    filename_heatmap = db.Column(db.String(120))
    prediction_model_id = db.Column(db.Integer, db.ForeignKey('prediction_model.id'))
    tile_id = db.Column(db.Integer, db.ForeignKey('tile.id'))

    def __repr__(self):
        return '<Prediction {}>'.format(self.id)  

