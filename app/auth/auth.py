# app/auth.py
import os, time
from typing import Optional, Dict, Any

import httpx
from fastapi import Header, HTTPException, Request
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_503_SERVICE_UNAVAILABLE
from jose import jwt

# ---- ENV (use consistent names everywhere) ----
COGNITO_REGION = os.getenv("COGNITO_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "")  # App Client ID

ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
JWKS_URL = f"{ISSUER}/.well-known/jwks.json"

# ---- JWKS cache ----
_jwks_cache: Optional[Dict[str, Any]] = None
_jwks_cached_at: float = 0.0
_JWKS_TTL_SECONDS = 3600

async def _get_jwks() -> Dict[str, Any]:
    global _jwks_cache, _jwks_cached_at
    now = time.time()
    if _jwks_cache is None or (now - _jwks_cached_at) > _JWKS_TTL_SECONDS:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(JWKS_URL)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                if _jwks_cache is None:
                    raise HTTPException(HTTP_503_SERVICE_UNAVAILABLE, f"JWKS fetch failed: {e}")
                return _jwks_cache
            _jwks_cache = resp.json()
            _jwks_cached_at = now
    return _jwks_cache

def _get_kid(token: str) -> str:
    try:
        header = jwt.get_unverified_header(token)
    except Exception:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Malformed token")
    kid = header.get("kid")
    if not kid:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Missing kid in token header")
    return kid

def _find_key_for_kid(kid: str, jwks: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            return k
    return None

async def _decode_id_token(token: str) -> Dict[str, Any]:
    jwks = await _get_jwks()
    kid = _get_kid(token)
    key = _find_key_for_kid(kid, jwks)
    if not key:
        # refresh once (rotation)
        global _jwks_cache, _jwks_cached_at
        _jwks_cache, _jwks_cached_at = None, 0.0
        jwks = await _get_jwks()
        key = _find_key_for_kid(kid, jwks)
        if not key:
            raise HTTPException(HTTP_401_UNAUTHORIZED, "Unknown signing key")

    try:
        claims = jwt.decode(
            token,
            key,                      # jose accepts JWK dict
            algorithms=["RS256"],     # Cognito uses RS256
            audience=COGNITO_CLIENT_ID,
            issuer=ISSUER,
        )
    except Exception as e:
        raise HTTPException(HTTP_401_UNAUTHORIZED, f"Invalid token: {e}")

    if claims.get("token_use") != "id":
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Wrong token_use; expected 'id'")
    return claims

# ---- Dependencies you can use per-route ----
async def require_user(request: Request, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.split(" ", 1)[1]
    claims = await _decode_id_token(token)
    request.state.user = claims     # Request is always present now
    return claims


async def optional_user(request: Request, authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """Allow anonymous GETs; enrich if a valid Bearer is present."""
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ", 1)[1]
    try:
        claims = await _decode_id_token(token)
        request.state.user = claims
        return claims
    except HTTPException:
        return None

def cognito_info() -> Dict[str, Any]:
    return {"issuer": ISSUER, "client_id_set": bool(COGNITO_CLIENT_ID)}
