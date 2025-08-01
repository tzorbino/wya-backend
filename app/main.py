from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import engine, Base
from app.models.post import Post  # or use import * if preferred
from app.models.vote import Vote
from app.models.comment import Comment
from app.routes import post_routes, comment_routes


Base.metadata.create_all(bind=engine)

app = FastAPI()

# Allow local dev frontend to connect
origins = ["http://localhost:3000", "http://localhost:5173"]  # adjust if using Vite/React

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "wya? backend is running"}

app.include_router(post_routes.router)
app.include_router(comment_routes.router)


for route in app.routes:
    print(f"{route.path} → {route.methods}")
# This will print all routes and their methods to the console