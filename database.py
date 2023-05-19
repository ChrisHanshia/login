from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = 'postgresql://hans:d8gVBjBx8X7IIp57385zhSX0RsudZj1K@dpg-chjh52bhp8u4bdvig6fg-a.singapore-postgres.render.com/login_database_tq1x'

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
