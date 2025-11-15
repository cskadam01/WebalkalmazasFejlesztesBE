from fastapi import FastAPI
from endpoints.users import router as users_router 
from endpoints.groups import router as groups_router

app = FastAPI()

app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(groups_router, prefix="/groups", tags=["Groups"])

@app.get("/")
def home():
    return {"message": "FastAPI is running 🚀"}