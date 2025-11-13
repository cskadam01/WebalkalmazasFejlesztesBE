from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel
from database.db import SessionLocal, get_db
from models.models import RoleEnum, Users
from config.password import generate_password 
import bcrypt
from config.token import create_access_token, get_current_user
import redis
import os
from dotenv import load_dotenv
import json

load_dotenv()


redis_url = os.getenv("REDIS_URL")



# Létrehozzuk a Redis-klienst az URL alapján
r = redis.from_url(
    redis_url,                  # 🔹 A teljes csatlakozási cím (host, port, jelszó, db)
    decode_responses=True,      # 🔹 A válaszokat automatikusan str-re alakítja (nem bytes-ra)
    socket_connect_timeout=5,   # 🔹 Ennyi mp-en belül kell létrejönnie a kapcsolatnak
    socket_timeout=5            # 🔹 Ennyi mp-en belül kell egy lekérdezésnek válaszolnia
)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

db = SessionLocal()


class LoginUser(BaseModel):
    email: str
    password: str

class CreateUser(BaseModel):
    email: str
    username: str
    full_name: str
    mobile: str
    role: RoleEnum



#Felhasználó authentikáció lekérés
@router.get("/auth")
def check_me(current_user : dict = Depends(get_current_user)):
    return current_user


#Felhasználó adatainak lekérése
@router.get("/user_details")
def get_user_data(current_user : dict = Depends(get_current_user),db: Session = Depends(get_db) ):

    user_details = db.query(Users).filter(Users.username == current_user["username"]).first()

    return{ 
        "id" : user_details.id,
        "full_name" :user_details.full_name,
        "email" :user_details.email,
        "username" :user_details.username,
        "mobile" :user_details.mobile,
        "role" :user_details.role,
    }


#Bejelentkezés
@router.post("/login")
def login (user: LoginUser, response : Response, db: Session = Depends(get_db) ):
    gotten_user = db.query(Users).filter(Users.email == user.email).first()
    if not gotten_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nem található felhasználó")
    

    stored_hash = gotten_user.password if isinstance(gotten_user.password, (bytes, bytearray)) else gotten_user.password.encode("utf-8")
    if not bcrypt.checkpw(user.password.encode("utf-8"), stored_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Hibás jelszó")
    
    data = {
        "sub": str(gotten_user.id),
        "username" : gotten_user.username,
        "role": gotten_user.role.value if isinstance(gotten_user.role, RoleEnum) else gotten_user.role,

    }
    
    token = create_access_token(data)

    response.set_cookie(
        key = "access_token",
        value = token,
        httponly= True,
        samesite= "lax",
        secure=True,
        max_age=60*120
    )

    session_key = f"session:{gotten_user.id}"  
    session_value = json.dumps({
        "token": token,
        "user_id": gotten_user.id,
        "username": gotten_user.username,
        "role": data["role"]
    })
    r.setex(session_key, 7200, session_value)

    return {"message": "sikeres bejelentkezés", "role" : gotten_user.role}



#Profil lértehozása csak admin által
@router.post("/create_user")
def register (new_user: CreateUser, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db), ):

        if current_user["role"]  != "admin":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nincs jogosultság")
        
        conflict = (
            db.query(Users)
            .filter(or_(
                Users.email == new_user.email,
                Users.username == new_user.username
            ))
            .first()
        )

        if conflict:
            if conflict.email == new_user.email:
                raise HTTPException(409, "Ez az email már foglalt.")
            if conflict.username == new_user.username:
                raise HTTPException(409, "Ez a felhasználónév már foglalt.")
            
             
        password = generate_password(12)
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


        new_user_obj = Users(
            username=new_user.username,
            full_name=new_user.full_name,
            password=hashed_pw,
            email=new_user.email,
            mobile=new_user.mobile,
            role=new_user.role
        )

        db.add(new_user_obj)
        db.commit()
        db.refresh(new_user_obj)

        return{
            "message" : "Sikeresen létrehozott felhasználó"

        }
