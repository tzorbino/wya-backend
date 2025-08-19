# main.py
import os
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine, Base
from app.models.post import Post
from app.models.vote import Vote
from app.models.comment import Comment
from app.routes import post_routes, comment_routes
from app.auth import require_user, optional_user, cognito_info

app = FastAPI()

# SwiftUI is a native client -> CORS is not enforced by iOS, allow all for simplicity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init DB
Base.metadata.create_all(bind=engine)

# Health & root
@app.get("/health")
def health():
    return {"status": "ok", **cognito_info()}

@app.get("/")
def read_root():
    return {"message": "wya? backend is running"}

# Public routers
app.include_router(post_routes.router)
app.include_router(comment_routes.router)

# Example protected endpoint
@app.get("/whoami")
def whoami(user: Dict[str, Any] = Depends(require_user)):
    return {"sub": user.get("sub"), "email": user.get("email"), "aud": user.get("aud")}

# Example that allows anonymous but enriches if signed in
@app.get("/feed")
def feed(request: Request, user: Optional[Dict[str, Any]] = Depends(optional_user)):
    # you can branch on `user is None`
    return {"items": [], "signed_in": bool(user)}

# Log routes on boot
for route in app.routes:
    try:
        print(f"{route.path} → {getattr(route, 'methods', {'GET'})}")
    except Exception:
        pass
