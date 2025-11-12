from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel
from database.db import SessionLocal, get_db
from models.models import RoleEnum, Users
import bcrypt
from config.token import create_acess_token


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

db = SessionLocal()


class LoginUser(BaseModel):
    email: str
    password: str





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
    
    token = create_acess_token(data)

    response.set_cookie(
        key = "acess_token",
        value = token,
        httponly= True,
        samesite= "lax",
        secure=True,
        max_age=60*120
    )

    return {"message": "sikeres bejelentkezés", "role" : gotten_user.role}
