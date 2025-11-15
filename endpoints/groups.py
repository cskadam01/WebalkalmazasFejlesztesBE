from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel
from database.db import SessionLocal, get_db
from models.models import RoleEnum, Users, Groups, Group_Members
from config.token import  get_current_user
from config.auth import  require_leader_or_admin


#------------- Endpoint felület ahol a csoportok endpointjait hozzuk létre -------------

router = APIRouter(
    tags=["Groups"]
)

db = SessionLocal()


class NewGroup(BaseModel):
    group_name : str
    group_description : str

class AddToGroup(BaseModel):
    user_to_add : int
    group_to_add: int



#Csoportok lekérése, a member és a group_leaderek csak a saját csoportjaikat, az admin az összes csoportot megkapják
@router.get("/groups")
def get_groups (current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    
    if current_user["role"] == "admin":
        user_groups = db.query(Groups).all()
    elif current_user["role"] == "group_leader":
        user_groups = db.query(Groups).filter(
            Groups.leader_id == current_user["id"]
        ).all()
    elif current_user["role"] == "member":
        user_groups = db.query(Groups).join(
            Group_Members, Group_Members.group_id == Groups.id).filter(
            Group_Members.user_id == current_user["id"] ).all()
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Valami hiba lépett fel a roleoknál, 'func: get_groups'")

    
    return [group.to_dict() for group in user_groups]

@router.get("/group/{group_id}")
def get_group(group_id : int, current_user: dict = Depends(get_current_user), db : Session = Depends(get_db)):
    

    if current_user["role"] == "admin":
        group = db.query(Groups).filter(Groups.id == group_id).first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nincs ilyen csoport")
    elif current_user["role"] == "group_leader":
        group = db.query(Groups).filter(and_(Groups.leader_id == current_user["id"], Groups.id == group_id)).first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nem jogosult ehhez a csoporthoz")
    elif current_user["role"] == "member":
        group = db.query(Groups).join(
                Group_Members, Group_Members.group_id == Groups.id).filter(
                Group_Members.user_id == current_user["id"], Groups.id == group_id).first()
        if not group:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nem jogosult ehhez a csoporthoz")



    members = []

    for i in group.members:
        member_data = {
            "member_id" : i.user.id,
            "member_name" :  i.user.username
        }
        members.append(member_data)
    
    

    return{
        "groupID":  group.id,
        "groupName":group.group_name,
        "groupLeader" : group.leader.username,
        "groupMembers" : members,
        "groupDesc" : group.group_description,
        "memberCount" : len(members)+1
    }





#Csoport létrehozása, a group leaderek és az adminok fognak tudni csportokat létrehozni
@router.post("/create-group")
def create_group(new_group : NewGroup, current_user: dict = Depends(require_leader_or_admin), db : Session = Depends(get_db)):

    conflict = db.query(Groups).filter(Groups.group_name == new_group.group_name).first()

    if conflict:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Foglalt csoport név")

    new_group_data =  Groups(
        leader_id = current_user["id"],
        group_name = new_group.group_name,
        group_description = new_group.group_description
    )

    db.add(new_group_data)
    db.commit()
    
    return{"message" : "Sikeres csoport létrehozás"}

#Emberek csoporthoz adása, admin és csoport leaderek fognak tudni membereket hozzá adni csoporokhoz
@router.post("/add-user-to-group")
def user_to_group(add_details: AddToGroup, current_user : dict = Depends(require_leader_or_admin), db : Session = Depends(get_db)):
    

    data = Group_Members(
        user_id = add_details.user_to_add,
        group_id = add_details.group_to_add
    )

    db.add(data)
    db.commit()

    return {"message" : "Sikeres hozzáadás"}


#Emberek  eltávolítása csoportokból, admin és csoport leaderek fognak tudni eltávolítani membereket a csoportokból
@router.delete("/remove-user-form-group/group/{group_id}/member/{user_id}")
def remove_user(group_id : int, user_id: int, current_user : dict = Depends(require_leader_or_admin), db : Session = Depends(get_db)):
    to_delete = db.query(Group_Members).filter(and_(Group_Members.user_id == user_id, Group_Members.group_id == group_id)).first()
    if not to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nincs ilyen felhasználó")

    if current_user["role"] == "group_leader":
        group_from = db.query(Groups).filter(Groups.id == group_id).first()
        if not group_from:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="nincs ilyen group")
        if group_from.leader_id == current_user["id"]:
            db.delete(to_delete)
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nincs jogosultság")  
           

    elif current_user["role"] == "admin":
            db.delete(to_delete)
           
    db.commit()
    return{"message" : "Sikeresen eltávolítottad a csoportból a felhasználót"}



#Teljes csoport törlése, leader és admin fogja törölni a csoportokat
@router.delete("/remove-group/{group_id}")
def remove_group(group_id : int, current_user: dict = Depends(require_leader_or_admin), db : Session = Depends(get_db)):
    
    group = db.query(Groups).filter(Groups.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Törölni kívánt csoport nem létezik")
    

    
    db.delete(group)
    db.commit()
