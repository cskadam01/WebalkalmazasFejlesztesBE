from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

database_url = os.getenv("DATABASE_URL")


#Kapcsolat létrehozása az adatbázissal
engine = create_engine(database_url)


#Ezzel a sessionnel fogunk tudni belenyúlni az adatbázisba
SessionLocal = sessionmaker(autocommit = False, autoflush= False, bind= engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



#Ezzel hozzuk létre az adatbázist leíró táblákat
Base = declarative_base()