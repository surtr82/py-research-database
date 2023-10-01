from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SelectField, BooleanField, FloatField, IntegerField, DateField, SubmitField
from wtforms.validators import ValidationError, NumberRange, DataRequired, Email, EqualTo, Length
from app.models import User


class UserLogin(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class UserRegistration(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class UserUpdate(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    organization = StringField('Organization', validators=[Length(min=0, max=128)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UserUpdate, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Please use a different email address.')    


class UserResetPasswordRequest(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class UserResetPassword(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')


class LiteratureForm(FlaskForm):
    site_id = SelectField('Site', coerce=int, validators=[DataRequired()])    
    author = StringField('Author', validators=[DataRequired()])
    year = IntegerField('Year')
    title = StringField('Title', validators=[DataRequired()])
    citation = StringField('Citation', validators=[DataRequired()])
    url = StringField('URL')

    submit = SubmitField('Save')


class PredictionForm(FlaskForm):
    prediction_model_id = SelectField('Model', coerce=int, validators=[DataRequired()])    
    tile_id = SelectField('Tile', coerce=int, validators=[DataRequired()])     
    site_id = SelectField('Site', coerce=int)       
    probability = FloatField('Probability', validators=[DataRequired()])
    file_heatmap = FileField("Heatmap")  
    submit = SubmitField('Save')


class PredictionModelForm(FlaskForm):
    repository_code_id = SelectField('Code Repository', coerce=int, validators=[DataRequired()])
    repository_data_id = SelectField('Data Repository', coerce=int, validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    file_validate_loss = FileField("Train & Validation Loss")
    file_validate_acc = FileField("Train & Validation Accuracy")   
    file_test_hist = FileField("Test Histogram")
    file_predict_hist = FileField("Prediction Histogram")    
    submit = SubmitField('Save')


class RepositoryCodeForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    repository = StringField('Repository', validators=[DataRequired()])
    branch = StringField('Branch', validators=[DataRequired()])
    commit = StringField('Commit', validators=[DataRequired()])
    gist = StringField('Gist', validators=[DataRequired()])
    submit = SubmitField('Save')


class RepositoryDataForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    repository = StringField('Repository', validators=[DataRequired()])
    branch = StringField('Branch', validators=[DataRequired()])
    commit = StringField('Commit', validators=[DataRequired()])
    no_images_train_tell = IntegerField('Training tell images', validators=[DataRequired()])
    no_images_train_other = IntegerField('Training other images', validators=[DataRequired()])
    no_images_validate_tell = IntegerField('Validation tell images', validators=[DataRequired()])
    no_images_validate_other = IntegerField('Validation other images', validators=[DataRequired()])
    no_images_test_tell = IntegerField('Test tell images', validators=[DataRequired()])
    no_images_test_other = IntegerField('Test other images', validators=[DataRequired()])
    no_images_predict_map = IntegerField('Prediction map images', validators=[DataRequired()])          
    corona_data = BooleanField('Corona Data')    
    submit = SubmitField('Save')


class SiteForm(FlaskForm):
    publication_no = IntegerField('Publication No.', validators=[NumberRange(min=1, max=1000)])
    sitename = StringField('Sitename')
    location = StringField('Location')
    province = StringField('Province')
    district = StringField('District')
    latitude = FloatField('Latitude')
    longitude = FloatField('Longitude')
    coordinates_confirmed = BooleanField('Coordinates confirmed')
    coordinates_outside_research_area = BooleanField('Coordinates confirmed')
    shape_id = SelectField('Shape', coerce=int, validators=[DataRequired()])
    est_tell_diameter = StringField('Est. Tell Diameter')
    est_lowertown_diameter = StringField('Est. Lower Town Diameter')
    est_tell_height = StringField('Est. Tell Height')    
    corona_is_overbuilt = BooleanField('Corona is overbuilt')
    corona_is_destroyed = BooleanField('Corona is destroyed')
    corona_has_quality_issue = BooleanField('Corona has Quality Issue')
    bing_is_overbuilt = BooleanField('Bing is overbuilt')
    bing_is_destroyed = BooleanField('Bing is destroyed')
    bing_has_quality_issue = BooleanField('Bing has Quality Issue')
    looted = BooleanField('Looted')
    dating = StringField('Dating')        
    bibliography = StringField('Bibliography') 
    tay_project = StringField('TAY-Project')
    file_bing_image = FileField('Satellite image') 
    file_corona_image = FileField('Corona image')    
    submit = SubmitField('Save')


class TileForm(FlaskForm):
    latitude = FloatField('Latitude', validators=[DataRequired()])
    longitude = FloatField('Longitude', validators=[DataRequired()])
    site_id = SelectField('Site', coerce=int, validators=[DataRequired()])    
    file_bing_image = StringField('Satellite image', validators=[DataRequired()])
    submit = SubmitField('Save')

