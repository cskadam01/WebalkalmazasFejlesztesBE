from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from enum import Enum as PyEnum

Base = declarative_base() 



#Előre meghatározott role-ok előkészítése
class RoleEnum(PyEnum):
    ADMIN = "admin"
    GROUP_LEADER = "group_leader"
    MEMBER = "member"


#Fehasználó Tábla definiálása
class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(50))
    password = Column(String(50))
    email = Column(String(50), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    mobile = Column(String(50))
    role = Column(Enum(RoleEnum), nullable=False)


    #Kapcsolatok
    # csoportok, amiket ő vezet
    groups_led = relationship("Groups", back_populates="leader")
    # csoporttagságok (ahol tagként szerepel)
    group_memberships = relationship("Group_Members", back_populates="user", cascade="all, delete-orphan")
    # skillek, amik ehhez a userhez tartoznak
    user_skills = relationship("User_Skills", back_populates="user", cascade="all, delete-orphan")



#Skillek tábla definiálása
class Skills(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    skill_name = Column(String(50))
    user_skills = relationship("User_Skills", back_populates="skill", cascade="all, delete-orphan")



class Groups(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    leader_id = Column(Integer, ForeignKey("users.id"))
    group_name = Column(String(50))
    group_description = Column(Text)

    leader = relationship("Users", back_populates="groups_led")
    members = relationship("Group_Members", back_populates="group", cascade="all, delete-orphan")



class Group_Members(Base):
    __tablename__ = 'group_members'
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), primary_key=True)

    user = relationship("Users", back_populates="group_memberships")
    group = relationship("Groups", back_populates="members")




class User_Skills(Base):
    __tablename__ = 'user_skills'
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)
    skill_level = Column(Integer)

    user = relationship("Users", back_populates="user_skills")
    skill = relationship("Skills", back_populates="user_skills")