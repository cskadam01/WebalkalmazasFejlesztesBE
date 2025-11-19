from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel
from config.auth import require_admin
from database.db import get_db
from sqlalchemy.orm import Session
from models.models import Skills, User_Skills

router = APIRouter(
    tags=["Skills"]
)


class NewSkill(BaseModel):
    skill_name: str

class SkillLevel(BaseModel):
    skill_level: int




@router.post("/new-skill")
def add_new_skill(new_skill : NewSkill, current_user: dict = Depends(require_admin), db : Session = Depends(get_db)):
    add_skill = Skills(
        skill_name = new_skill
    )

    db.add(add_new_skill)
    db.commit()
    return {"Sikeresen létrehoztál egy új skillt"}

@router.post("/add-skill-to-user/{userID}/skill/{skillID}")
def add_skill_to_user(userID : int, skillID: int, skill: SkillLevel, current_user : dict = Depends(require_admin), db : Session = Depends(get_db)):

    data = User_Skills(
        user_id = userID,
        skill_id = skillID,
        skill_level = skill.skill_level
    )

    db.add(data)
    db.commit()
    return {"Sikeresen hozzáadtad a skill-t a felhasználóhoz"}

@router.put("/change-level/{userID}/skills/{skillID}")
def change_level(userID : int, skillID : int, gotten_skill_level : SkillLevel, current_user : dict = Depends(require_admin), db : Session = Depends(get_db) ):
    
    level_to_change = db.query(User_Skills).filter(User_Skills.skill_id == skillID, User_Skills.user_id == userID).first()
    if not level_to_change:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="nincs ilyen skillje ennek az embernek")

    level_to_change.skill_level = gotten_skill_level

   
    db.commit()
    db.refresh(level_to_change)

    return {f"Level sikeresen átírva {level_to_change.skill_level} --> {gotten_skill_level}"}

@router.get("/get-all-skills")
def get_all_skills( current_user : dict = Depends(require_admin), db : Session = Depends(get_db)):

    skills = db.query(Skills).all()
    if not skills:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Egy skill sem található")

    all_skills = []

    for skill in skills :
        skill_data = {
            "skillId" : skill.id,
            "skillName" : skill.skill_name
        }
        all_skills.append(skill_data)

    return all_skills

@router.delete("/remove-skill/{skillID}/user/{userID}")
def remove_skill(userID : int, skillID : int, current_user : dict = Depends(require_admin), db : Session = Depends(get_db) ):
    to_delete = db.query(User_Skills).filter(User_Skills.skill_id == skillID, User_Skills.user_id == userID).first()
    if not to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Törölni kívánt skill, vagy felhasználó nem található")


    db.delete(to_delete)
    db.commit()

    return{"Skill sikeresen eltávolítva a felhasználótól"}
