from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import engine, Base
from app.models.post import Post
from app.models.vote import Vote
from app.models.comment import Comment
from app.routes import post_routes, comment_routes

app = FastAPI()

origins = ["http://localhost:5173", "https://localhost:5173", "http://localhost:3000", "https://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/test-cors")
def test_cors():
    return {"message": "CORS is working"}

# ✅ Move this BELOW middleware setup
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "wya? backend is running"}

app.include_router(post_routes.router)
app.include_router(comment_routes.router)


for route in app.routes:
    print(f"{route.path} → {route.methods}")
