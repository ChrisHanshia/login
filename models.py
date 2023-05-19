from database import Base
from sqlalchemy import Column, Integer, String, Boolean


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    date_of_birth = Column(String)
    register_number = Column(String, unique=True)
    phone_number = Column(String)
    address = Column(String)
    course = Column(String)
    gender = Column(String)
