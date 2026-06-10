from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError  # <-- FIX: Added robust DB error catching
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from models import User, get_db

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
SECRET_KEY = "super-secret-hackathon-key"
ALGORITHM = "HS256"

router = APIRouter(prefix="/auth")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise credentials_exception
        return user
    except OperationalError:
        raise HTTPException(status_code=500, detail="System Schema Error: Please contact support.")

@router.post("/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_pw = pwd_context.hash(user_data.password)
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_pw,
            full_name=user_data.full_name,
            is_admin=False
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        access_token = create_access_token(data={"sub": str(new_user.id), "is_admin": new_user.is_admin})
        return {"access_token": access_token, "token_type": "bearer", "user_id": new_user.id, "is_admin": new_user.is_admin}
        
    except OperationalError as e:
        db.rollback()
        # Cleanly handles the exact crash you just experienced!
        raise HTTPException(status_code=500, detail="Database schema mismatch detected. Database requires an upgrade.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == user_data.email).first()
        if not user or not pwd_context.verify(user_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        access_token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "is_admin": user.is_admin}
        
    except OperationalError as e:
        # Cleanly handles schema mismatches during login
        raise HTTPException(status_code=500, detail="Database schema mismatch detected. Database requires an upgrade.")