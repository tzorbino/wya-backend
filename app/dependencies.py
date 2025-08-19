# app/dependencies.py
from typing import Optional, Dict, Any
from fastapi import Header, Request
import os

# --- ENV name compatibility (supports old and new names) ---
COGNITO_REGION        = os.getenv("COGNITO_REGION", "us-east-1")
COGNITO_USER_POOL_ID  = os.getenv("COGNITO_USER_POOL_ID") or os.getenv("USER_POOL_ID") or ""
COGNITO_CLIENT_ID     = os.getenv("COGNITO_CLIENT_ID")    or os.getenv("COGNITO_AUDIENCE") or ""

# Expose what auth.py expects to find in the environment
os.environ.setdefault("COGNITO_REGION", COGNITO_REGION)
os.environ.setdefault("COGNITO_USER_POOL_ID", COGNITO_USER_POOL_ID)
os.environ.setdefault("COGNITO_CLIENT_ID", COGNITO_CLIENT_ID)

# --- Reuse the new auth logic ---
from .auth import optional_user, require_user

# Back-compat for existing routers that import get_current_user
async def get_current_user(request: Request, authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """Returns None for anonymous; otherwise decoded claims dict."""
    # Call the auth helper using its new signature (request first)
    return await optional_user(request, authorization)

# If a route should be strictly authenticated, import this instead:
get_required_user = require_user
