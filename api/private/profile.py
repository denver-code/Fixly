from fastapi import APIRouter, HTTPException, Request

from api.models import User
from app.core.jwt import FastJWT


profile_router = APIRouter(prefix="/profile")



@profile_router.get("/")
async def profile_event(request: Request):
    # TODO: Make middleware to get user from token
    token = await FastJWT().decode(request.headers["Authorization"])
    user = await User.get(token.id)
    if not user:
        raise HTTPException(401, "Unauthorized")
    
    return {
        "id": str(user.id),
        "username": user.username,
    }