from fastapi import FastAPI
from endpoints.users import router as users_router 

app = FastAPI()

app.include_router(users_router, prefix="/users", tags=["Users"])

@app.get("/")
def home():
    return {"message": "FastAPI is running 🚀"}