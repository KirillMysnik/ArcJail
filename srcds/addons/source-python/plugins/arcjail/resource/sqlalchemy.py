from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import config
from .paths import ARCJAIL_DATA_PATH


engine = create_engine(config['database']['uri'].format(
    arcjail_data_path=ARCJAIL_DATA_PATH,
))
Base = declarative_base()
Session = sessionmaker(bind=engine)
