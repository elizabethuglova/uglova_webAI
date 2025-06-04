from sqlalchemy import Column, Integer, String
from data.db_session import SqlAlchemyBase
from flask_login import UserMixin

class Users(SqlAlchemyBase, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
