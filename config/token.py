from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv
import os
load_dotenv()

expire_time = os.getenv("ACCESS_TOKEN_EXPIRE_MIN")
secret_pass = os.getenv("SECRET_KEY")
token_algorithm = os.getenv("ALGORITHM")

def create_acess_token(data: dict, expires_minutes: int = expire_time):
    #Lemásoljuk a kapott adatokat
    to_encode = data.copy()
    #A jelenlegi időhöz hozzáadjuk a lejárati időt
    expire = datetime.utcnow=() + timedelta(minutes=expires_minutes)
    #Kiegészítjük a kapott adaotokat azzal, hogy mikor fog lehárni a token
    to_encode.update({"exp" : expire})
    return jwt.encode(to_encode, secret_pass, algorithm=token_algorithm )