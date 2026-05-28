from sqlalchemy import Column, Integer, String, Float, VARCHAR
from database import Base

class DB_user(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_settings_id = privileges = Column(Integer, notnull=True)
    username = Column(String, unique=True, notnull=True)
    password = Column(String, notnull=True)
    privileges = Column(Integer, notnull=True)

class DB_user_settings(Base):
    __tablename__ = ("usersettings")
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    jsonsettings = Column(VARCHAR(1000))