#The main application for this FastApi aplication
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
#to prevent something that isnt app connect with our app
from jose import JWTError, jwt
from datetime import datetime,timedelta
import time
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Annotated
from models import User, Debt
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import func

app=FastAPI()

#MIDDLEWARE & AUTHENTICATION STARTUP
#----------------------------------------------------------------------

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")

origins =[
    "http://localhost:3000",
    "http://localhost:8000",
]
#Which sites have acces to CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

#DATABASE CODE
#----------------------------------------------------------------------

#Creating pydantic models
#Using for validating data before using real query or before printing
class DebtBase(BaseModel):
    title: str
    receiver: str
    amount: float
    user_id: int


class UserBase(BaseModel):
    username:str
    password: str

#dependency of our database
#Trying to get our db but closing connection always
async def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close_all()

pwd_context=CryptContext(schemes=["bcrypt"], deprecated="auto")

#SECRET JWT
#node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
#----------------------------------------------------------------------

SECRET_KEY="287c9891908ac1e3893332989d2ea439410f444968e4c1689fa61701f1379c36"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=20

#LOCAL FUNCTIONS WITH MODELS
#----------------------------------------------------------------------

def get_user_by_username(db:Session, username:str):
    return db.query(User).filter(User.username==username).first()

def create_user(db:Session, user:UserBase):
    hashed_password=pwd_context.hash(user.password)
    db_user=User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    return 'User added'

db_dependency=Annotated[Session, Depends(get_db)]

##USER DATABASE FUNCTIONS
#----------------------------------------------------------------------

#@app.post("/users/", status_code=status.HTTP_201_CREATED)
#We get all the data from user validation UserBase
#async def create_user(user:UserBase, db:db_dependency):
    #db_user=models.User(**user.dict()) 
    #in this way it would send all data and is not best practice
    #db_user=User(username=user.username)
    #We can change models.User to User when we import it from models 
    #db.add(db_user)
    #db.commit()

#@app.get("/users/{user_id}", status_code=status.HTTP_200_OK)
#async def read_user(user_id: int, db:db_dependency):
    #user=db.query(User).filter(User.id == user_id).first()
    #if user is None:
    #    raise HTTPException(status_code=404, detail='User not found')
    #return user

#AUTHENTICATION AND REGISTRATION
#----------------------------------------------------------------------

@app.post("/register")
async def register_user(user: UserBase, db:db_dependency):
    db_user=get_user_by_username(db,username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db=db,user=user)

def authenticate_user(username: str, password: str, db: Session):
    user=db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not pwd_context.verify(password,user.hashed_password):
        return False
    return user

def create_token(data:dict, expires_delta:timedelta | None=None):
    to_encode=data.copy()
    if expires_delta:
        expire=datetime.utcnow() + expires_delta
    else:
        expire=datetime.utcnow()+timedelta(minutes=15)
    to_encode.update({"exp":expire})
    enocded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return enocded_jwt

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm=Depends(),db: Session=Depends(get_db)):
    user=authenticate_user(form_data.username, form_data.password,db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token=create_token(data={"sub":user.username},expires_delta=access_token_expires)
    return {"access_token":access_token, "token_type":"bearer"}
    #Typo in this place caused problems with token verification


async def verify_token(token: str=Depends(oauth2_scheme)):
    try:
        #our decoded token
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username:str=payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="Token is invalid or expired")
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Token is invalid or expired")

@app.get("/verify-token", response_model=dict)
def verify_user_token(token:str = Depends(verify_token)):
    return {"message":"Token is valid"}

#DEBTS DATABASE FUNCTIONS
#----------------------------------------------------------------------

@app.post("/protected/debts/",status_code=status.HTTP_201_CREATED)
async def create_debt(debt: DebtBase, db:db_dependency, token: str=Depends(verify_token)):
    username=token.get("sub")
    user=db.query(User).filter(User.username==username).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_debt=Debt(title=debt.title, receiver=debt.receiver, amount=debt.amount, user_id=debt.user_id)
    db.add(db_debt)
    db.commit()

@app.get("/protected/debts/all/",status_code=status.HTTP_200_OK)
async def read_user_debts(db:db_dependency, token: str=Depends(verify_token)):
    username=token.get("sub")
    user=db.query(User).filter(User.username==username).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    debts=db.query(Debt).filter(Debt.user_id==user.id).all()
    
    if debts is None:
        raise HTTPException(status_code=404, detail='Debts not found')
    if not debts:
        return {"all_user_debts":[]}
    
    return {"all_user_debts":debts}

@app.delete("/protected/debts/{debt_id}", status_code=status.HTTP_200_OK)
async def delete_debt(debt_id: int, db:db_dependency, token: str=Depends(verify_token)):
    username=token.get("sub")
    user=db.query(User).filter(User.username==username).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_debt=db.query(Debt).filter(Debt.id==debt_id).first()
    
    if db_debt is None:
        raise HTTPException(status_code=404, detail='Debt not found')
    
    db.delete(db_debt)
    db.commit()

@app.get("/protected/debts/sum/", status_code=status.HTTP_200_OK)
async def calc_debt_sum(db:db_dependency, token: str=Depends(verify_token)):
    username=token.get("sub")
    user=db.query(User).filter(User.username==username).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    total_debt=db.query(func.round(func.sum(Debt.amount),2)).filter(Debt.user_id==user.id).scalar() or 0

    return {"totalDebt":total_debt}

@app.get("/protected/users", status_code=status.HTTP_200_OK)
async def get_all_users(db:db_dependency, token: str=Depends(verify_token)):
    username=token.get("sub")
    user=db.query(User).filter(User.username==username).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    all_user=db.query(User).all()
    
    return {"allUsers":all_user}

#----------------------------------------------------------------------