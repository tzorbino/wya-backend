# main.py
import os
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED
import httpx
from jose import jwt

from app.db import engine, Base
from app.models.post import Post
from app.models.vote import Vote
from app.models.comment import Comment
from app.routes import post_routes, comment_routes

# ======== COGNITO CONFIG (update env vars in Render when these change) ========
REGION = os.getenv("COGNITO_REGION", "us-east-1")
USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "us-east-1_bL6O1YL3r")        # ← from Xcode
CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "29kli1gar9601v0oks7oe37io0")       # ← from Xcode

ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"
JWKS_URL = f"{ISSUER}/.well-known/jwks.json"

# ======== APP BOOT ========
app = FastAPI()

origins = [
    "http://localhost:5173", "https://localhost:5173",
    "http://localhost:3000", "https://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB after middleware
Base.metadata.create_all(bind=engine)

# ======== JWKS cache & verification ========
_jwks_cache: Optional[Dict[str, Any]] = None

async def get_jwks() -> Dict[str, Any]:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(JWKS_URL)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache

def _get_kid(token: str) -> str:
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    if not kid:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Missing kid in token header")
    return kid

def _find_key_for_kid(kid: str, jwks: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            return k
    return None

async def verify_id_token_from_auth_header(authorization: Optional[str]) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization[7:]

    jwks = await get_jwks()
    kid = _get_kid(token)
    key = _find_key_for_kid(kid, jwks)
    if not key:
        # Key rotated: refresh once
        global _jwks_cache
        _jwks_cache = None
        jwks = await get_jwks()
        key = _find_key_for_kid(kid, jwks)
        if not key:
            raise HTTPException(HTTP_401_UNAUTHORIZED, "Unknown signing key")

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=[key.get("alg", "RS256")],
            audience=CLIENT_ID,  # must match your App Client ID
            issuer=ISSUER,       # must match your pool issuer
        )
    except Exception as e:
        raise HTTPException(HTTP_401_UNAUTHORIZED, f"Invalid token: {e}")

    if claims.get("token_use") != "id":
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Wrong token_use; expected 'id'")
    return claims

async def require_auth(request: Request) -> Dict[str, Any]:
    claims = await verify_id_token_from_auth_header(request.headers.get("authorization"))
    request.state.user = claims  # stash for handlers
    return claims

# ======== ROUTES ========
@app.get("/test-cors")
def test_cors():
    return {"message": "CORS is working"}

@app.get("/")
def read_root():
    return {"message": "wya? backend is running"}

# Public routers (as you had)
app.include_router(post_routes.router)
app.include_router(comment_routes.router)

# Example protected endpoint (optional quick test)
@app.get("/whoami", dependencies=[Depends(require_auth)])
def whoami(request: Request):
    c = request.state.user
    return {"sub": c.get("sub"), "email": c.get("email"), "aud": c.get("aud")}

# Print route map
for route in app.routes:
    try:
        print(f"{route.path} → {getattr(route, 'methods', {'GET'})}")
    except Exception:
        pass
