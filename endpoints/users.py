from sqlalchemy.orm import Session
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
    role: str





@router.post("/login")
def login (user: LoginUser, response : Response, db: Session = Depends(get_db) ):
    gotten_user = db.query(Users).filter(Users.email == user.email).first()
    if not gotten_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nem található felhasználó")
    

    stored_hash = gotten_user.password if isinstance(gotten_user.password, (bytes, bytearray)) else gotten_user.password.encode("utf-8")
    if not bcrypt.checkpw(user.password.encode("utf-8"), stored_hash):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Helytelen felhasználó")
    
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

    #Token átalakítása json fromátumra
    token_json  = json.dumps(token)

    #Azonosító létrehozása
    session_key = f"session: {gotten_user.id}"

    #Lejárati idővel eltároljuk
    r.setex(token_json, 7200, session_key)

    return {"message": "sikeres bejelentkezés", "role" : gotten_user.role}


@router.post("/create_user")
def register (new_user: CreateUser, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db), ):
    try:
        if current_user["role"]  != "admin":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nincs jogosultság")
        
        get_user = db.query(Users).filter(new_user.email == Users.email).first()

        if  new_user.email == get_user.email:
            raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail= "Foglalt email cím")
        
        if  new_user.full_name == get_user.full_name:
            raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail= "Foglalt teljes név")


        if  new_user.username == get_user.username:
            raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail= "Foglalt felhasználónév")
        
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
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valami hiba lépett fel")