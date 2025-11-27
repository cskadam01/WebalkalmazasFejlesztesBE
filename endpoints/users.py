from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel
from database.db import SessionLocal, get_db
from models.models import RoleEnum, Users
from config.password import generate_password 
import bcrypt
from config.token import create_access_token, get_current_user
from config.auth import require_admin, require_leader_or_admin
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
    specialty : str
    role: RoleEnum



#Felhasználó authentikáció lekérés
@router.get("/auth")
def check_me(current_user : dict = Depends(get_current_user)):
    return current_user


#Felhasználó adatainak lekérése
@router.get("/user-details")
def get_user_data(current_user : dict = Depends(get_current_user),db: Session = Depends(get_db) ):

    user_details = db.query(Users).filter(Users.username == current_user["username"]).first()

    groups = []
    for i in user_details.group_memberships:
        groups.append(i.group.group_name)

    return{ 
        "id" : user_details.id,
        "full_name" :user_details.full_name,
        "email" :user_details.email,
        "username" :user_details.username,
        "mobile" :user_details.mobile,
        "role" :user_details.role,
        "specialty" : user_details.specialty,
        "groups" :  groups
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
        "userId" : gotten_user.id,
        "username" : gotten_user.username,
        "role": gotten_user.role.value if isinstance(gotten_user.role, RoleEnum) else gotten_user.role,
    }
    
    token = create_access_token(data)

    response.set_cookie(
        key = "access_token",
        value = token,
        httponly= True,
        samesite= "none",
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


@router.get("/all-users")
def get_all_user(current_user : dict = Depends(require_leader_or_admin), db: Session = Depends(get_db)):
    all_useres = db.query(Users).all()

    all_user_data = []

    for user in all_useres:
        user_dict = {
            "fullName" : user.full_name,
            "speciality" : user.specialty
        }
        all_user_data.append(user_dict)

    return all_user_data

@router.get("/get-user/{userID}")
def get_user (userID : int, currnet_user : dict = Depends(get_current_user), db : Session = Depends(get_db)):
    
    user_details = db.query(Users).filter(Users.id == userID).first()
    if not user_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Felhasználó nem található")
    

    user_skills = []

    users_group = []
    for i in user_details.group_memberships:
        users_group.append(i.group.group_name)
    
    
    user_data = {
        "username" : user_details.username,
        "fullname" :  user_details.full_name,
        "role" : user_details.role,
        "groups" : users_group,
        "specialty" : user_details.specialty,
        "skills" : user_skills

    }

    return user_data




#Profil lértehozása csak admin által
@router.post("/create-user")
def register (new_user: CreateUser, current_user: dict = Depends(require_admin), db: Session = Depends(get_db), ):

        
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
            password = hashed_pw.decode("utf-8"),
            email=new_user.email,
            mobile=new_user.mobile,
            role=new_user.role,
            specialty = new_user.specialty
        )

        db.add(new_user_obj)
        db.commit()
        db.refresh(new_user_obj)

        return{
            "message" : "Sikeresen létrehozott felhasználó",
            "pass" : password
        }


@router.post("/logout")
def logout ( response : Response, current_user : dict = Depends(get_current_user)):
    
    session_key = f"session:{current_user['id']}"
    success = r.delete(session_key)
    if success == 1:
        print("törlés sikeres volt")
    else:
        print("nem sikerült törölni redisből a tokent")


    response.delete_cookie("access_token")

    return{"message" : "Sikeres kijelentkezés"}