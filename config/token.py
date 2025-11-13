from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv
import os, json, redis
from fastapi import Request, HTTPException, status

load_dotenv()



REDIS_URL = os.getenv("REDIS_URL")
r = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
)



expire_time = int(os.getenv("ACCESS_TOKEN_EXPIRE_MIN"))
secret_pass = os.getenv("SECRET_KEY")
token_algorithm = os.getenv("ALGORITHM")

def create_access_token(data: dict, expires_minutes: int = expire_time):
    #Lemásoljuk a kapott adatokat
    to_encode = data.copy()
    #A jelenlegi időhöz hozzáadjuk a lejárati időt
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    #Kiegészítjük a kapott adaotokat azzal, hogy mikor fog lehárni a token
    to_encode.update({"exp" : expire})
    return jwt.encode(to_encode, secret_pass, algorithm=token_algorithm )


#kapott token dekódolása
def decode_token(token: str) -> dict:
    try:
        return jwt.decode(secret_pass, token, algorithms=[token_algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Érvénytelen token")


def get_current_user(request : Request):

    #Lekérjük a tokent a böngészőtől
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nem található token")
    
    #A kapott tokent dekódoljuk
    payload = decode_token(token)

    #Kinyerjük a felhasználó id-t a tokenből
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Hibás token")

    session_key = f"session: {user_id}"
    stored = r.get(session_key)
    if not stored:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Lejárt vagy hiányzó session")
    
    try:
        data = json.loads(stored)           
        stored_token = data.get("token") or stored
    except json.JSONDecodeError:
        stored_token = stored                # sima token-stringet tároltál

    if stored_token != token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session-token eltérés")


    return {
        "id": int(user_id),
        "username": payload.get("username"),
        "role": payload.get("role"),
    }