from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

from models import Base

load_dotenv()
db = SQLAlchemy(model_class=Base, pool_recycle=280)
