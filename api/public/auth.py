from fastapi import APIRouter
from pydantic import BaseModel

from api.models import User
from app.core.config import config
from app.core.jwt import FastJWT
from app.core.password_hash import get_password_hash, verify_password
from fastapi import HTTPException, status

auth_router = APIRouter(prefix="/auth")


class UserAuth(BaseModel):
    username: str
    password: str


@auth_router.post("/signup")
async def signup(payload: UserAuth ):
    if await User.find_one(User.username == payload.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    password = get_password_hash(payload.password)
    user = User(
        username=payload.username,
        password_hash=password
    )
    await user.insert()
    return {"message": "User created successfully"}


@auth_router.post("/signin")
async def signin(payload: UserAuth):
    db_user = await User.find_one(User.username == payload.username)
    if not db_user or not verify_password(payload.password, db_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    
    jwt_token = await FastJWT().encode(optional_data={
        "id": str(db_user.id),
        "username": payload.username,
    })

    return {"token": jwt_token}