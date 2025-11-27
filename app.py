from fastapi import FastAPI
from endpoints.users import router as users_router 
from endpoints.groups import router as groups_router
from endpoints.skills import router as skills_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
        allow_origins=[
        "https://gymdatabase-129e2.web.app",
        "http://localhost:5173"
    ],
  # vagy a saját domained
    allow_credentials=True,  # ⬅⬅⬅ FONTOS: kell a sütikhez!
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(groups_router, prefix="/groups", tags=["Groups"])
app.include_router(skills_router, prefix="/skills", tags=["Skills"])
@app.get("/")
def home():
    return {"message": "FastAPI is running 🚀"}