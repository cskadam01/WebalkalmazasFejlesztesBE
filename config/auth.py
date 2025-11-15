from fastapi import Depends, HTTPException, status
from config.token import get_current_user

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nincs jogosultság")
    return current_user

def require_leader_or_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin" and current_user["role"] != "group_leader":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nincs jogosultság")
    return current_user