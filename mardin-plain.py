from app import app, db
from app.models import User, Tile, Site, RepositoryCode, RepositoryData, PredictionModel, Prediction

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Tile': Tile, 'Site': Site, 'RepositoryCode': RepositoryCode, 'RepositoryData': RepositoryData, 'PredictionModel': PredictionModel, 'Prediction': Prediction }

     
