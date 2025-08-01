import os
import requests
from fastapi import Header, HTTPException, status, Request
from typing import Optional
from jose import jwt, JWTError
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Read from .env
COGNITO_REGION = os.getenv("COGNITO_REGION")
USER_POOL_ID = os.getenv("USER_POOL_ID")
COGNITO_AUDIENCE = os.getenv("COGNITO_AUDIENCE")  # App Client ID

COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}"
jwks_url = f"{COGNITO_ISSUER}/.well-known/jwks.json"
jwks = requests.get(jwks_url).json()


def get_current_user(
    authorization: Optional[str] = Header(None),
    request: Request = None
):
    if not authorization or not authorization.startswith("Bearer "):
        # Allow anonymous GET requests
        if request and request.method == "GET":
            return None
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]

    try:
        decoded = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=COGNITO_AUDIENCE,
            issuer=COGNITO_ISSUER
        )

        print("✅ Decoded Token", decoded)

        return {
            "id": decoded["sub"],
            "email": decoded.get("email"),
            "username": decoded.get("preferred_username")
        }

    except JWTError as e:
        print("❌ JWT verification failed:", e)
        print("🔍 Token that failed:", token)
        raise HTTPException(status_code=401, detail="Invalid or expired token")
