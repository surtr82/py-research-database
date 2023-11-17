from app import app, db
from app.email import send_password_reset_email
from app.forms import UserLogin, UserRegistration, UserUpdate, UserResetPasswordRequest, UserResetPassword, PredictionForm, PredictionModelForm, RepositoryCodeForm, RepositoryDataForm, SiteForm, TileForm
from app.models import User, Tile, Site, RepositoryCode, RepositoryData, PredictionModel, Prediction, CertaintyScore, CoronaConditionScore, BingConditionScore
from flask import render_template, abort, flash, redirect, url_for, request, send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
import imghdr
import json
import os
import shutil
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename


@app.route('/')
@app.route('/index')
@login_required
def index():
    sites = Site.query.filter().all()

    site_list = []
    for site in sites:
        site_element = {}
        site_element['long'] = site.longitude
        site_element['lat'] = site.latitude
        site_element['id'] = site.id
        site_element['name'] = site.location
        site_list.append(site_element)
    
    return render_template('index.html', title='Home', site_json=site_list)


@app.route('/navigation/file/<crud_id>')
@login_required
def navigation_file(crud_id):
    if crud_id == 'create':
        crud_filename = 'create.png'
    elif crud_id == 'read':
        crud_filename = 'read.png'
    elif crud_id == 'update':
        crud_filename = 'update.png'
    elif crud_id == 'delete':
        crud_filename = 'delete.png'
    else:
        crud_filename = 'goto.png'

    return send_from_directory(os.path.join(app.config['DIRECTORY_NAVIGATION_READ']), str(crud_filename))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = UserLogin()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('user_login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = UserRegistration()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('user_registration.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_profile.html', user=user)


@app.route('/user_update', methods=['GET', 'POST'])
@login_required
def user_update():
    form = UserUpdate(current_user.username, current_user.email)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.organization = form.organization.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user_update'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.organization.data = current_user.organization
    return render_template('user_update.html', title='Update Profile', form=form)    


@app.route('/user_reset_password_request', methods=['GET', 'POST'])
def user_reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = UserResetPasswordRequest()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('user_reset_password_request.html',
                           title='Reset Password', form=form)    


@app.route('/user_reset_password/<token>', methods=['GET', 'POST'])
def user_reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = UserResetPassword()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('user_reset_password.html', form=form)
                           

@app.route('/predictions/<prediction_model_id>/<min_probability>/<max_probability>/<shows_tell>')
@login_required
def prediction_list(prediction_model_id, min_probability, max_probability, shows_tell):
    
    if int(prediction_model_id) != 0:
        prediction_model = PredictionModel.query.get_or_404(prediction_model_id)
    
    if int(prediction_model_id) == 0:
        prediction_model = PredictionModel.query.first()
        prediction_model_id = prediction_model.id
    
    prediction_models = PredictionModel.query.all()

    if int(min_probability) == 0:
        min_probability = 50

    if int(max_probability) == 0:
        max_probability = 100

    if shows_tell == '1': 
        predictions = Prediction.query.join(Prediction.tile).join(Tile.site).filter(Prediction.prediction_model_id==prediction_model_id).filter(Prediction.probability.between(min_probability, max_probability)).all()
    elif shows_tell == '2':
        predictions = Prediction.query.join(Prediction.tile).outerjoin(Tile.site).filter(Prediction.prediction_model_id==prediction_model_id).filter(Prediction.probability.between(min_probability, max_probability)).filter(Tile.site == None).all()
    else:
        predictions = Prediction.query.filter(Prediction.prediction_model_id==prediction_model_id).filter(Prediction.probability.between(min_probability, max_probability)).all()

    return render_template('prediction_list.html', title='Predictions', predictions=predictions, prediction_models=prediction_models, prediction_model_id=prediction_model_id, min_probability=min_probability, max_probability=max_probability, shows_tell=shows_tell) 


@app.route('/prediction/read/<prediction_id>', methods=['GET', 'POST'])
@login_required
def prediction_read(prediction_id):
    prediction = Prediction.query.get_or_404(prediction_id)
    return render_template('prediction_form_read.html', title='Prediction', prediction=prediction) 


@app.route('/prediction/create', methods=['GET', 'POST'])
@login_required
def prediction_create():
    form = PredictionForm()

    prediction_models = PredictionModel.query.all()
    prediction_model_list = [(prediction_model.id, prediction_model.description) for prediction_model in prediction_models] 
    form.prediction_model_id.choices = prediction_model_list     

    sites = Site.query.all()
    sites_list = [('0', '-- None --')] + [(site.id, site.location) for site in sites] 
    form.site_id.choices = sites_list     

    tiles = Tile.query.all() 
    tile_list = [(tile.id, '{:.4f}'.format(tile.latitude) + ', {:.4f}'.format(tile.longitude)) for tile in tiles] 
    form.tile_id.choices = tile_list 

    if form.validate_on_submit():

        file_heatmap_transmitted = False
        file_heatmap = request.files['file_heatmap']
        file_heatmap.seek(0, os.SEEK_END)
        if file_heatmap.tell() != 0:
            file_heatmap.seek(0, 0)
            file_heatmap_transmitted = True          
            filename_heatmap = file_heatmap.filename
            extension_heatmap = os.path.splitext(filename_heatmap)[1]
            if extension_heatmap not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)   

        prediction = Prediction()
        prediction.prediction_model_id = form.prediction_model_id.data
        prediction.tile_id = form.tile_id.data
        prediction.probability = form.probability.data

        site_id = form.site_id.data
        tile = Tile.query.get_or_404(prediction.tile_id)
        if str(site_id) == '0':
            tile.site_id = None
        else:
            tile.site_id = site_id

        if file_heatmap_transmitted:
            prediction.filename_heatmap= 'BNG [{:.4f}'.format(prediction.latitude) + ', {:.4f}'.format(prediction.longitude) + ']' + extension_heatmap

        db.session.add(prediction)
        db.session.commit()

        directory = os.path.join(app.config['DIRECTORY_PREDICTION_CREATE'], str(prediction.prediction_model_id), str(prediction.id))
        if os.path.exists(directory) == False:
            os.mkdir(directory)                       

        if file_heatmap_transmitted:
            file_heatmap.save(os.path.join(directory, prediction.filename_heatmap))

        flash('Prediction added.')
        return redirect(url_for('prediction_list', prediction_model_id=0, min_probability=50, max_probability=100, shows_tell=0))    
    return render_template('prediction_form_create.html', title='Add Prediction', form=form)


@app.route('/prediction/update/<prediction_id>', methods=['GET', 'POST'])
@login_required
def prediction_update(prediction_id):
    form = PredictionForm()    
    prediction = Prediction.query.get_or_404(prediction_id)

    prediction_models = PredictionModel.query.all()
    prediction_model_list = [(prediction_model.id, prediction_model.description) for prediction_model in prediction_models] 
    form.prediction_model_id.choices = prediction_model_list     

    sites = Site.query.all()
    sites_list = [(0, '-- None --')] + [(site.id, site.location) for site in sites] 
    form.site_id.choices = sites_list     

    tiles = Tile.query.all() 
    tile_list = [(tile.id, '{:.4f}'.format(tile.latitude) + ', {:.4f}'.format(tile.longitude)) for tile in tiles] 
    form.tile_id.choices = tile_list 

    if form.validate_on_submit():
   
        file_heatmap_transmitted = False
        file_heatmap = request.files['file_heatmap']
        file_heatmap.seek(0, os.SEEK_END)
        if file_heatmap.tell() != 0:
            file_heatmap.seek(0, 0)
            file_heatmap_transmitted = True          
            filename_heatmap = file_heatmap.filename
            extension_heatmap = os.path.splitext(filename_heatmap)[1]
            if extension_heatmap not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)   

        prediction.prediction_model_id = form.prediction_model_id.data
        prediction.tile_id = form.tile_id.data
        prediction.probability = form.probability.data

        site_id = form.site_id.data
        tile = Tile.query.get_or_404(prediction.tile_id)
        if str(site_id) == '0':
            tile.site_id = None
        else:
            tile.site_id = site_id

        if file_heatmap_transmitted:
            prediction.filename_heatmap= 'BNG [{:.4f}'.format(prediction.latitude) + ', {:.4f}'.format(prediction.longitude) + ']' + extension_heatmap

        db.session.commit()

        directory = os.path.join(app.config['DIRECTORY_PREDICTION_CREATE'], str(prediction.prediction_model_id), str(prediction.id))
        if os.path.exists(directory) == False:
            os.mkdir(directory)                       

        if file_heatmap_transmitted:
            file_heatmap.save(os.path.join(directory, prediction.filename_heatmap))

        flash('Prediction updated.')
        return redirect(url_for('prediction_list', prediction_model_id=0, min_probability=50, max_probability=100, shows_tell=0))    
    elif request.method == 'GET':
        form.prediction_model_id.data = prediction.prediction_model_id        
        form.tile_id.data = prediction.tile_id
        form.probability.data = prediction.probability
        form.site_id.data = prediction.tile.site_id
    return render_template('prediction_form_update.html', title='Update Prediction', prediction=prediction, form=form) 


@app.route('/prediction/delete/<prediction_id>', methods=['POST'])
@login_required
def prediction_delete(prediction_id):
    prediction = Prediction.query.get_or_404(prediction_id)

    directory = os.path.join(app.config['DIRECTORY_PREDICTION_CREATE'], str(prediction.prediction_model_id), str(prediction.id))
    if os.path.exists(directory):
        shutil.rmtree(directory)

    db.session.delete(prediction)
    db.session.commit()

    flash('Prediction deleted.')
    return redirect(url_for('prediction_list'))


@app.route('/prediction/file/heatmap/<prediction_id>')
@login_required
def prediction_file_heatmap(prediction_id):
    prediction = Prediction.query.get_or_404(prediction_id)
    print(app.config['DIRECTORY_PREDICTION_READ'])
    return send_from_directory(os.path.join(app.config['DIRECTORY_PREDICTION_READ'], str(prediction.prediction_model_id), str(prediction.id)), prediction.filename_heatmap)


@app.route('/models')
@login_required
def prediction_model_list():
    prediction_models = PredictionModel.query.all()
    return render_template('prediction_model_list.html', title='Models', prediction_models=prediction_models) 


@app.route('/model/<prediction_model_id>', methods=['GET'])
@login_required
def prediction_model_read(prediction_model_id):
    prediction_model = PredictionModel.query.get_or_404(prediction_model_id)

    prediction_list = []
    predictions = Prediction.query.filter(Prediction.prediction_model_id==prediction_model_id).all()
    for prediciton in predictions:
        prediciton_element = {}
        prediciton_element['probability'] = prediciton.probability
        prediction_list.append(prediciton_element)

    return render_template('prediction_model_form_read.html', title='Model', prediction_model=prediction_model, prediction_list=prediction_list)


@app.route('/model/create', methods=['GET', 'POST'])
@login_required
def prediction_model_create():
    form = PredictionModelForm()

    repositories = RepositoryCode.query.all() 
    repository_list = [(repository.id, repository.description) for repository in repositories] 
    form.repository_code_id.choices = repository_list 

    repositories = RepositoryData.query.all() 
    repository_list = [(repository.id, repository.description) for repository in repositories] 
    form.repository_data_id.choices = repository_list 

    if form.validate_on_submit():

        file_validate_loss_transmitted = False
        file_validate_loss = request.files['file_validate_loss']
        file_validate_loss.seek(0, os.SEEK_END)
        if file_validate_loss.tell() != 0:
            file_validate_loss.seek(0, 0)               
            file_validate_loss_transmitted = True          
            filename_validate_loss = file_validate_loss.filename
            extension_validate_loss = os.path.splitext(filename_validate_loss)[1]
            if extension_validate_loss not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)   

        file_validate_acc_transmitted = False
        file_validate_acc = request.files['file_validate_acc']
        file_validate_acc.seek(0, os.SEEK_END)
        if file_validate_acc.tell() != 0:
            file_validate_acc.seek(0, 0)                  
            file_validate_acc_transmitted = True          
            filename_validate_acc = file_validate_acc.filename
            extension_validate_acc = os.path.splitext(filename_validate_acc)[1]
            if extension_validate_acc not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)   

        file_test_hist_transmitted = False
        file_test_hist = request.files['file_test_hist']
        file_test_hist.seek(0, os.SEEK_END)
        if file_test_hist.tell() != 0:
            file_test_hist.seek(0, 0)                
            file_test_hist_transmitted = True        
            filename_test_hist = file_test_hist.filename
            extension_test_hist = os.path.splitext(filename_test_hist)[1]
            if extension_test_hist not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)   

        file_predict_hist_transmitted = False
        file_predict_hist = request.files['file_predict_hist']
        file_predict_hist.seek(0, os.SEEK_END)
        if file_predict_hist.tell() != 0:
            file_predict_hist.seek(0, 0)                
            file_predict_hist_transmitted = True
            filename_predict_hist = file_predict_hist.filename
            extension_predict_hist = os.path.splitext(filename_predict_hist)[1]
            if extension_predict_hist not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)   
  
        prediction_model = PredictionModel()
        prediction_model.repository_code_id = form.repository_code_id.data
        prediction_model.repository_data_id = form.repository_data_id.data        
        prediction_model.description = form.description.data
        prediction_model.date = form.date.data

        if file_validate_loss_transmitted:
            prediction_model.filename_validate_loss = 'validate_loss' + extension_validate_loss

        if file_validate_acc_transmitted:
            prediction_model.filename_validate_acc = 'validate_acc' + extension_validate_acc

        if file_test_hist_transmitted:
            prediction_model.filename_test_hist = 'test_hist' + extension_test_hist

        if file_predict_hist_transmitted:
            prediction_model.filename_predict_hist = 'predict_hist' + extension_predict_hist            

        db.session.add(prediction_model)
        db.session.commit()

        directory = os.path.join(app.config['DIRECTORY_PREDICTION_CREATE'], str(prediction_model.id))
        if os.path.exists(directory) == False:
            os.mkdir(directory)     

        directory = os.path.join(app.config['DIRECTORY_PREDICTIONMODEL_CREATE'], str(prediction_model.id))
        if os.path.exists(directory) == False:
            os.mkdir(directory)                       

        if file_validate_loss_transmitted:
            file_validate_loss.save(os.path.join(directory, prediction_model.filename_validate_loss))

        if file_validate_acc_transmitted:
            file_validate_acc.save(os.path.join(directory, prediction_model.filename_validate_acc))

        if file_test_hist_transmitted:
            file_test_hist.save(os.path.join(directory, prediction_model.filename_test_hist))

        if file_predict_hist_transmitted:
            file_predict_hist.save(os.path.join(directory, prediction_model.filename_predict_hist))

        flash('Model added.')
        return redirect(url_for('prediction_model_list'))    
    return render_template('prediction_model_form_create.html', title='Add Model', form=form)


@app.route('/model/update/<prediction_model_id>', methods=['GET', 'POST'])
@login_required
def prediction_model_update(prediction_model_id):
    form = PredictionModelForm()
    prediction_model = PredictionModel.query.get_or_404(prediction_model_id)

    repositories = RepositoryCode.query.all() 
    repository_list = [(repository.id, repository.description) for repository in repositories] 
    form.repository_code_id.choices = repository_list 

    repositories = RepositoryData.query.all() 
    repository_list = [(repository.id, repository.description) for repository in repositories] 
    form.repository_data_id.choices = repository_list 

    if form.validate_on_submit():

        file_validate_loss_transmitted = False
        file_validate_loss = request.files['file_validate_loss']
        file_validate_loss.seek(0, os.SEEK_END)
        if file_validate_loss.tell() != 0:
            file_validate_loss.seek(0, 0)
            file_validate_loss_transmitted = True          
            filename_validate_loss = file_validate_loss.filename
            extension_validate_loss = os.path.splitext(filename_validate_loss)[1]
            if extension_validate_loss not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)   

        file_validate_acc_transmitted = False
        file_validate_acc = request.files['file_validate_acc']
        file_validate_acc.seek(0, os.SEEK_END)
        if file_validate_acc.tell() != 0:
            file_validate_acc.seek(0, 0)            
            file_validate_acc_transmitted = True          
            filename_validate_acc = file_validate_acc.filename
            extension_validate_acc = os.path.splitext(filename_validate_acc)[1]
            if extension_validate_acc not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)   

        file_test_hist_transmitted = False
        file_test_hist = request.files['file_test_hist']
        file_test_hist.seek(0, os.SEEK_END)
        if file_test_hist.tell() != 0:
            file_test_hist.seek(0, 0)              
            file_test_hist_transmitted = True        
            filename_test_hist = file_test_hist.filename
            extension_test_hist = os.path.splitext(filename_test_hist)[1]
            if extension_test_hist not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)   

        file_predict_hist_transmitted = False
        file_predict_hist = request.files['file_predict_hist']
        file_predict_hist.seek(0, os.SEEK_END)
        if file_predict_hist.tell() != 0:
            file_predict_hist.seek(0, 0)                 
            file_predict_hist_transmitted = True
            filename_predict_hist = file_predict_hist.filename
            extension_predict_hist = os.path.splitext(filename_predict_hist)[1]
            if extension_predict_hist not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)   
  
        prediction_model.repository_code_id = form.repository_code_id.data
        prediction_model.repository_data_id = form.repository_data_id.data        
        prediction_model.description = form.description.data
        prediction_model.date = form.date.data

        if file_validate_loss_transmitted:
            prediction_model.filename_validate_loss = 'validate_loss' + extension_validate_loss

        if file_validate_acc_transmitted:
            prediction_model.filename_validate_acc = 'validate_acc' + extension_validate_acc

        if file_test_hist_transmitted:
            prediction_model.filename_test_hist = 'test_hist' + extension_test_hist

        if file_predict_hist_transmitted:
            prediction_model.filename_predict_hist = 'predict_hist' + extension_predict_hist            

        db.session.commit()

        directory = os.path.join(app.config['DIRECTORY_PREDICTION_CREATE'], str(prediction_model.id))
        if os.path.exists(directory) == False:
            os.mkdir(directory)     

        directory = os.path.join(app.config['DIRECTORY_PREDICTIONMODEL_CREATE'], str(prediction_model.id))
        if os.path.exists(directory) == False:
            os.mkdir(directory)                       

        if file_validate_loss_transmitted:
            file_validate_loss.save(os.path.join(directory, prediction_model.filename_validate_loss))

        if file_validate_acc_transmitted:
            file_validate_acc.save(os.path.join(directory, prediction_model.filename_validate_acc))

        if file_test_hist_transmitted:
            file_test_hist.save(os.path.join(directory, prediction_model.filename_test_hist))

        if file_predict_hist_transmitted:
            file_predict_hist.save(os.path.join(directory, prediction_model.filename_predict_hist))

        flash('Model updated.')
        return redirect(url_for('prediction_model_list'))    
    elif request.method == 'GET':
        form.repository_code_id.data = prediction_model.repository_code_id
        form.repository_data_id.data = prediction_model.repository_data_id       
        form.description.data = prediction_model.description
        form.date.data = prediction_model.date
    return render_template('prediction_model_form_update.html', title='Update Model', prediction_model=prediction_model, form=form) 


@app.route('/model/delete/<prediction_model_id>', methods=['POST'])
@login_required
def prediction_model_delete(prediction_model_id):
    prediction_model = PredictionModel.query.get_or_404(prediction_model_id)

    directory = os.path.join(app.config['DIRECTORY_PREDICTION_CREATE'], str(prediction_model.id))
    if os.path.exists(directory):
        shutil.rmtree(directory)    

    directory = os.path.join(app.config['DIRECTORY_PREDICTIONMODEL_CREATE'], str(prediction_model.id))
    if os.path.exists(directory):
        shutil.rmtree(directory)       

    db.session.delete(prediction_model)
    db.session.commit()

    flash('Model deleted.')
    return redirect(url_for('prediction_model_list'))


@app.route('/model/file/validate_loss/<prediction_model_id>')
@login_required
def prediction_model_file_validate_loss(prediction_model_id):
    prediction_model = PredictionModel.query.get_or_404(prediction_model_id)
    print(app.config['DIRECTORY_PREDICTIONMODEL_READ'])
    return send_from_directory(os.path.join(app.config['DIRECTORY_PREDICTIONMODEL_READ'], str(prediction_model.id)), prediction_model.filename_validate_loss)


@app.route('/model/file/validate_acc/<prediction_model_id>')
@login_required
def prediction_model_file_validate_acc(prediction_model_id):
    prediction_model = PredictionModel.query.get_or_404(prediction_model_id)
    return send_from_directory(os.path.join(app.config['DIRECTORY_PREDICTIONMODEL_READ'], str(prediction_model.id)), prediction_model.filename_validate_acc)


@app.route('/model/file/test_hist/<prediction_model_id>')
@login_required
def prediction_model_file_test_hist(prediction_model_id):
    prediction_model = PredictionModel.query.get_or_404(prediction_model_id)
    return send_from_directory(os.path.join(app.config['DIRECTORY_PREDICTIONMODEL_READ'], str(prediction_model.id)), prediction_model.filename_test_hist)


@app.route('/model/file/predict_hist/<prediction_model_id>')
@login_required
def prediction_model_file_predict_hist(prediction_model_id):
    prediction_model = PredictionModel.query.get_or_404(prediction_model_id)
    return send_from_directory(os.path.join(app.config['DIRECTORY_PREDICTIONMODEL_READ'], str(prediction_model.id)), prediction_model.filename_predict_hist)


@app.route('/repositories/code')
@login_required
def repository_code_list():
    repositories = RepositoryCode.query.all()
    return render_template('repository_code_list.html', repositories=repositories) 


@app.route('/repository/code/<repository_id>', methods=['GET', 'POST'])
@login_required
def repository_code_read(repository_id):
    repository = RepositoryCode.query.get_or_404(repository_id)
    return render_template('repository_code_form_read.html', title='Code Repository', repository=repository)


@app.route('/repository/code/create', methods=['GET', 'POST'])
@login_required
def repository_code_create():
    form = RepositoryCodeForm()
    if form.validate_on_submit():
        repository = RepositoryCode()
        repository.description = form.description.data
        repository.date = form.date.data
        repository.repository = form.repository.data
        repository.branch = form.branch.data
        repository.commit = form.commit.data
        repository.gist = form.gist.data
        db.session.add(repository)
        db.session.commit()
        flash('Repository added.')
        return redirect(url_for('repository_code_list'))    
    return render_template('repository_code_form_create.html', title='Add Code Repository', form=form)


@app.route('/repository/code/update/<repository_id>', methods=['GET', 'POST'])
@login_required
def repository_code_update(repository_id):
    form = RepositoryCodeForm()
    repository = RepositoryCode.query.get_or_404(repository_id)
    if form.validate_on_submit():
        repository.description = form.description.data
        repository.date = form.date.data
        repository.repository = form.repository.data
        repository.branch = form.branch.data
        repository.commit = form.commit.data
        repository.gist = form.gist.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('repository_code_list', repository_id=repository.id))
    elif request.method == 'GET':
        form.description.data = repository.description
        form.date.data = repository.date
        form.repository.data = repository.repository
        form.branch.data = repository.branch
        form.commit.data = repository.commit
        form.gist.data = repository.gist
    return render_template('repository_code_form_update.html', title='Update Code Repository', form=form, repository=repository) 


@app.route('/repository/code/delete/<repository_id>', methods=['POST'])
@login_required
def repository_code_delete(repository_id):
    repository = RepositoryCode.query.get_or_404(repository_id)
    db.session.delete(repository)
    db.session.commit()
    flash('Repository deleted.')
    return redirect(url_for('repository_code_list'))


@app.route('/repositories/data')
@login_required
def repository_data_list():
    repositories = RepositoryData.query.all()
    return render_template('repository_data_list.html', repositories=repositories) 


@app.route('/repository/data/create', methods=['GET', 'POST'])
@login_required
def repository_data_create():
    form = RepositoryDataForm()
    if form.validate_on_submit():
        repository = RepositoryData()
        repository.description = form.description.data
        repository.date = form.date.data
        repository.repository = form.repository.data
        repository.branch = form.branch.data
        repository.commit = form.commit.data
        repository.corona_data = form.corona_data.data
        repository.no_images_train_tell = form.no_images_train_tell.data
        repository.no_images_train_other = form.no_images_train_other.data  
        repository.no_images_validate_tell = form.no_images_validate_tell.data
        repository.no_images_validate_other = form.no_images_validate_other.data
        repository.no_images_test_tell = form.no_images_test_tell.data
        repository.no_images_test_other = form.no_images_test_other.data
        repository.no_images_predict_map = form.no_images_predict_map.data              
        db.session.add(repository)
        db.session.commit()
        flash('Repository added.')
        return redirect(url_for('repository_data_list'))    
    return render_template('repository_data_form_create.html', title='Add Data Repository', form=form)


@app.route('/repository/data/<repository_id>', methods=['GET', 'POST'])
@login_required
def repository_data_read(repository_id):
    repository = RepositoryData.query.get_or_404(repository_id)
    return render_template('repository_data_form_read.html', title='Data Repository', repository=repository)


@app.route('/repository/data/update/<repository_id>', methods=['GET', 'POST'])
@login_required
def repository_data_update(repository_id):
    form = RepositoryDataForm()
    repository = RepositoryData.query.get_or_404(repository_id)
    if form.validate_on_submit():
        repository.description = form.description.data
        repository.date = form.date.data
        repository.repository = form.repository.data
        repository.branch = form.branch.data
        repository.commit = form.commit.data
        repository.corona_data = form.corona_data.data
        repository.no_images_train_tell = form.no_images_train_tell.data
        repository.no_images_train_other = form.no_images_train_other.data  
        repository.no_images_validate_tell = form.no_images_validate_tell.data
        repository.no_images_validate_other = form.no_images_validate_other.data
        repository.no_images_test_tell = form.no_images_test_tell.data
        repository.no_images_test_other = form.no_images_test_other.data
        repository.no_images_predict_map = form.no_images_predict_map.data            
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('repository_data_list', repository_id=repository.id))
    elif request.method == 'GET':
        form.description.data = repository.description
        form.date.data = repository.date
        form.repository.data = repository.repository
        form.branch.data = repository.branch
        form.commit.data = repository.commit
        form.corona_data.data = repository.corona_data
        form.no_images_train_tell.data = repository.no_images_train_tell
        form.no_images_train_other.data = repository.no_images_train_other  
        form.no_images_validate_tell.data = repository.no_images_validate_tell
        form.no_images_validate_other.data = repository.no_images_validate_other
        form.no_images_test_tell.data = repository.no_images_test_tell
        form.no_images_test_other.data = repository.no_images_test_other
        form.no_images_predict_map.data = repository.no_images_predict_map            
    return render_template('repository_data_form_update.html', title='Update Data Repository', form=form, repository=repository) 


@app.route('/repository/data/delete/<repository_id>', methods=['POST'])
@login_required
def repository_data_delete(repository_id):
    repository = RepositoryData.query.get_or_404(repository_id)
    db.session.delete(repository)
    db.session.commit()
    flash('Repository deleted.')
    return redirect(url_for('repository_data_list'))


@app.route('/sites')
@login_required
def site_list():
    sites = Site.query.order_by(Site.publication_no).all()
    return render_template('site_list.html', sites=sites) 


@app.route('/site/<site_id>', methods=['GET'])
@login_required
def site_read(site_id):
    site = Site.query.get_or_404(site_id)
    return render_template('site_form_read.html', site=site) 


@app.route('/site/create', methods=['GET', 'POST'])
@login_required
def site_create():
    form = SiteForm()

    scores = CertaintyScore.query.all() 
    score_list = [(score.id, score.description) for score in scores] 
    form.certainty_score_id.choices = score_list 
    
    scores = CoronaConditionScore.query.all() 
    score_list = [(score.id, score.description) for score in scores] 
    form.corona_settlement_score_id.choices = score_list 

    scores = BingConditionScore.query.all() 
    score_list = [(score.id, score.description) for score in scores] 
    form.bing_settlement_score_id.choices = score_list 

    if form.validate_on_submit():

        file_bing_transmitted = False        
        file_bing_image = request.files['file_bing_image']
        file_bing_image.seek(0, os.SEEK_END)
        if file_bing_image.tell() != 0:
            file_bing_image.seek(0)
            file_bing_transmitted = True
            filename_bing_image = file_bing_image.filename
            extension_bing_image = os.path.splitext(filename_bing_image)[1]
            if extension_bing_image not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)   

        file_corona_transmitted = False
        file_corona_image = request.files['file_corona_image']
        file_corona_image.seek(0, os.SEEK_END)
        if file_corona_image.tell() != 0:       
            file_corona_image.seek(0)
            file_corona_transmitted = True
            filename_corona_image = file_corona_image.filename
            extension_corona_image = os.path.splitext(filename_corona_image)[1]
            if extension_corona_image not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)  

        site = Site()
        site.publication_no = form.publication_no.data
        site.sitename = form.sitename.data 
        site.location = form.location.data 
        site.province = form.province.data
        site.district = form.district.data
        site.latitude = form.latitude.data 
        site.longitude = form.longitude.data 
        site.est_tell_diameter = form.est_tell_diameter.data
        site.est_lowertown_diameter = form.est_lowertown_diameter.data
        site.est_tell_height = form.est_tell_height.data        
        site.is_registered = form.is_registered.data
        site.is_georeference_confirmed = form.is_georeference_confirmed.data
        site.is_georeference_outside_research_area = form.is_georeference_outside_research_area.data
        site.is_looted = form.is_looted.data
        site.certainty_score_id = form.certainty_score_id.data
        site.corona_condition_score_id = form.corona_condition_score_id.data
        site.bing_condition_score_id = form.bing_condition_score_id.data
        site.tay_project = form.tay_project.data
        site.bibliography = form.bibliography.data
                
        if file_bing_transmitted:
            site.filename_bing_image = 'BNG [{:.4f}'.format(site.latitude) + ', {:.4f}'.format(site.longitude) + ']' + extension_bing_image

        if file_corona_transmitted:
            site.filename_corona_image = 'CRN [{:.4f}'.format(site.latitude) + ', {:.4f}'.format(site.longitude) + ']' + extension_corona_image
            
        db.session.add(site)
        db.session.commit()

        directory = os.path.join(app.config['DIRECTORY_SITE_CREATE'], str(site.id))
        if os.path.exists(directory) == False:
            os.mkdir(directory)                       

        flash('Site added.')
        return redirect(url_for('site_list'))    
    return render_template('site_form_create.html', title='Add Site', form=form)


@app.route('/site/update/<site_id>', methods=['GET', 'POST'])
@login_required
def site_update(site_id):
    form = SiteForm()
    site = Site.query.get_or_404(site_id)

    scores = CertaintyScore.query.all() 
    score_list = [(score.id, score.description) for score in scores] 
    form.certainty_score_id.choices = score_list 
    
    scores = CoronaConditionScore.query.all() 
    score_list = [(score.id, score.description) for score in scores] 
    form.corona_settlement_score_id.choices = score_list 

    scores = BingConditionScore.query.all() 
    score_list = [(score.id, score.description) for score in scores] 
    form.bing_settlement_score_id.choices = score_list 

    if form.validate_on_submit():
        file_bing_transmitted = False        
        file_bing_image = request.files['file_bing_image']
        file_bing_image.seek(0, os.SEEK_END)
        if file_bing_image.tell() != 0:
            file_bing_image.seek(0)
            file_bing_transmitted = True
            filename_bing_image = file_bing_image.filename
            extension_bing_image = os.path.splitext(filename_bing_image)[1]
            if extension_bing_image not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)   

        file_corona_transmitted = False
        file_corona_image = request.files['file_corona_image']
        file_corona_image.seek(0, os.SEEK_END)
        if file_corona_image.tell() != 0:       
            file_corona_image.seek(0)
            file_corona_transmitted = True
            filename_corona_image = file_corona_image.filename
            extension_corona_image = os.path.splitext(filename_corona_image)[1]
            if extension_corona_image not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)   

        site.publication_no = form.publication_no.data
        site.sitename = form.sitename.data 
        site.location = form.location.data 
        site.province = form.province.data
        site.district = form.district.data
        site.latitude = form.latitude.data 
        site.longitude = form.longitude.data 
        site.est_tell_diameter = form.est_tell_diameter.data
        site.est_lowertown_diameter = form.est_lowertown_diameter.data
        site.est_tell_height = form.est_tell_height.data        
        site.is_registered = form.is_registered.data
        site.is_georeference_confirmed = form.is_georeference_confirmed.data
        site.is_georeference_outside_research_area = form.is_georeference_outside_research_area.data
        site.is_looted = form.is_looted.data
        site.certainty_score_id = form.certainty_score_id.data
        site.corona_condition_score_id = form.corona_condition_score_id.data
        site.bing_condition_score_id = form.bing_condition_score_id.data
        site.tay_project = form.tay_project.data
        site.bibliography = form.bibliography.data

        if file_bing_transmitted:
            site.filename_bing_image = 'BNG [{:.4f}'.format(site.latitude) + ', {:.4f}'.format(site.longitude) + ']' + extension_bing_image

        if file_corona_transmitted:
            site.filename_corona_image = 'CRN [{:.4f}'.format(site.latitude) + ', {:.4f}'.format(site.longitude) + ']' + extension_corona_image
        db.session.commit()

        directory = os.path.join(app.config['DIRECTORY_SITE_CREATE'], str(site.id))
        if os.path.exists(directory) == False:
            os.mkdir(directory)                       

        if file_bing_transmitted:
            file_bing_image.save(os.path.join(directory, site.filename_bing_image))

        if file_corona_transmitted:
            file_corona_image.save(os.path.join(directory, site.filename_corona_image))

        flash('Site updated.')
        return redirect(url_for('site_list'))    
    elif request.method == 'GET':
        form.publication_no.data = site.publication_no
        form.sitename.data = site.sitename
        form.location.data = site.location
        form.province.data = site.province
        form.district.data = site.district
        form.latitude.data = site.latitude
        form.longitude.data = site.longitude
        form.est_tell_diameter.data = site.est_tell_diameter
        form.est_lowertown_diameter.data = site.est_lowertown_diameter
        form.est_tell_height.data = site.est_tell_height
        form.is_registered.data = site.is_registered        
        form.is_georeference_confirmed.data = site.is_georeference_confirmed
        form.is_georeference_outside_research_area.data = site.is_georeference_outside_research_area
        form.is_looted.data = site.is_looted
        form.certainty_score_id.data = site.certainty_score_id
        form.corona_condition_score_id.data = site.corona_condition_score_id
        form.bing_condition_score_id.data = site.bing_condition_score_id
        form.tay_project.data = site.tay_project
        form.bibliography.data = site.bibliography
        
    return render_template('site_form_update.html', title='Update Site', form=form)


@app.route('/site/delete/<site_id>', methods=['POST'])
@login_required
def site_delete(site_id):
    site = Site.query.get_or_404(site_id)
    db.session.delete(site)
    db.session.commit()

    directory = os.path.join(app.config['DIRECTORY_SITE_CREATE'], str(site.id))
    if os.path.exists(directory):
        shutil.rmtree(directory)

    flash('Site deleted.')
    return redirect(url_for('site_list'))


@app.route('/site/<site_id>/tile/<tile_id>', methods=['POST'])
@login_required
def site_tile_delete(site_id, tile_id):
    tile = Tile.query.get_or_404(tile_id)
    tile.site_id = None
    db.session.commit()

    site = Site.query.get_or_404(site_id)
    return render_template('site_form_read.html', site=site)     
    

@app.route('/site/image/bing/<site_id>')
@login_required
def site_image_bing(site_id):
    site = Site.query.get_or_404(site_id)
    return send_from_directory(os.path.join(app.config['DIRECTORY_SITE_READ'], str(site.id)), site.filename_bing_image)


@app.route('/site/image/corona/<site_id>')
@login_required
def site_image_corona(site_id):
    site = Site.query.get_or_404(site_id)
    return send_from_directory(os.path.join(app.config['DIRECTORY_SITE_READ'], str(site.id)), site.filename_corona_image)


@app.route('/tiles/<latitude>/<longitude>')
@login_required
def tile_list(latitude, longitude):

    filename = 'Map [latitude%, longitude%].png'
    filename = filename.replace('latitude', latitude).replace('longitude', longitude)

    tiles = Tile.query.filter(Tile.image_filename.like(filename)).all()
    return render_template('tile_list.html', tiles=tiles, latitude=latitude, longitude=longitude) 


@app.route('/tile/image/bing/<tile_id>')
@login_required
def tile_image_bing(tile_id):
    tile = Tile.query.get_or_404(tile_id)
    return send_from_directory(app.config['DIRECTORY_TILE_BING_READ'], tile.image_filename)


@app.route('/tile/image/corona/<tile_id>')
@login_required
def tile_image_corona(tile_id):
    tile = Tile.query.get_or_404(tile_id)
    return send_from_directory(app.config['DIRECTORY_TILE_CORONA_READ'], tile.image_filename)


@app.route('/bingmaps/overview')
@login_required
def bingmaps_overview():
    return render_template('bingmaps.html') 


@app.route('/bingmaps/coordinate/<latitude>/<longitude>')
@login_required
def bingmaps_coordinate(latitude, longitude):
    return render_template('bingmaps.html', latitude=latitude, longitude=longitude)    
