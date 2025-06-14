from flask import Flask
from dotenv import load_dotenv
import os
from models.database import init_db
from controllers.line_controller import line_bp
from utils.get_menu_items import create_rich_menu

load_dotenv()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
init_db(app)

app.register_blueprint(line_bp)

if __name__ == "__main__":
    create_rich_menu()
    app.run(host='0.0.0.0', port=5001)

