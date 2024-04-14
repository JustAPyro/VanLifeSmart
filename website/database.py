from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

from models import Base

load_dotenv()
db = SQLAlchemy(model_class=Base, engine_options={
    'connect_args': {
        'connect_timeout': 10
    }
})
