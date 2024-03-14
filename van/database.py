import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine

from models import Base

# Load environment variables for path
load_dotenv()

# If the data folder doesn't exist at the given location, create it
Path(f'{os.getenv("VLS_DATA_PATH")}').mkdir(parents=True, exist_ok=True)

# Create the database
engine = create_engine(
        f'sqlite:///{os.getenv("VLS_DATA_PATH")}/database.db',
        connect_args={"check_same_thread": False})

# Instantiate all database tables
Base.metadata.create_all(engine)