#SQL Alchemy to able create tables defined in here to our SQL database
from sqlalchemy import Boolean, Column, Integer, String, Float
from database import Base
from database import engine
#importig our database base in here

class User(Base):
    __tablename__='users'
    id=Column(Integer, primary_key=True, index=True, autoincrement=True)
    username=Column(String(50), unique=True)
    hashed_password=Column(String(500), nullable=False)


class Debt(Base):
    __tablename__='debts'
    id=Column(Integer, primary_key=True, index=True, autoincrement=True)
    title=Column(String(100))
    receiver=Column(String(50))
    amount=Column(Float)
    user_id=Column(Integer) #That is our foreign key related to user database

Base.metadata.create_all(bind=engine)