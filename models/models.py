from sqlalchemy import Boolean, Enum, ForeignKey, PrimaryKeyConstraint, Integer, String, Column, Text
from enum import Enum as PyEnum
from db import Base



#Előre meghatározott role-ok előkészítése
class RoleEnum(PyEnum):
    ADMIN = "admin"
    GROUP_LEADER = "group_leader"
    MEMBER = "member"


#Fehasználó Tábla definiálása
class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50))
    full_name = Column(String(50))
    password = Column(String(50))
    email = Column(String(50))
    mobile = Column(String(50))
    role = Column(Enum(RoleEnum), nullable=False)

#Skillek tábla konfigurálása
class Skills(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    skill_name = Column(String(50))

class Groups(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    leader_id = Column(Integer, ForeignKey("users.id"))
    group_name = Column(String(50))
    group_description = Column(Text)

class Group_Members(Base):
    __tablename__ = 'group_members'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))