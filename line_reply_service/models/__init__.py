from flask_sqlalchemy import SQLAlchemy
from .users import User
from .line_binding_user import LineBindingUser

db = SQLAlchemy()

def init_models(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
