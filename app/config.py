import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'y0u-w1ll-n3v3r-gue$$'
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://mardin:m4rd1n@localhost:3306/mardin-plain'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['p.guggisberg@gmx.ch']
    DIRECTORY_NAVIGATION_READ = 'static/files/navigation'
    DIRECTORY_PREDICTION_READ = 'static/files/prediction'
    DIRECTORY_PREDICTION_CREATE = 'app/static/files/prediction'      
    DIRECTORY_PREDICTIONMODEL_READ = 'static/files/predictionmodel'
    DIRECTORY_PREDICTIONMODEL_CREATE = 'app/static/files/predictionmodel'  
    DIRECTORY_SITE_READ = 'static/files/site'
    DIRECTORY_SITE_CREATE = 'app/static/files/site'
    DIRECTORY_TILE_BING_READ = 'static/files/tile/bing'
    DIRECTORY_TILE__BING_CREATE = 'app/static/files/tile/bing'
    DIRECTORY_TILE_CORONA_READ = 'static/files/tile/corona'
    DIRECTORY_TILE__COORNA_CREATE = 'app/static/files/tile/corona'    
    UPLOAD_MAX_CONTENT_LENGTH = 1024 * 1024
    UPLOAD_EXTENSIONS = ['.jpg', '.png', '.svg', '.pdf']


