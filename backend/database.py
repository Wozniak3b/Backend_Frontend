from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
#Importing from sqlalchemy basic things

URL_DATABSE="mysql+pymysql://root:@localhost:3306/DebtApp"

engine=create_engine(URL_DATABSE)

SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base=declarative_base()