from fastapi import APIRouter
from api.public.auth import auth_router

api_router = APIRouter(prefix="/api")

public_router = APIRouter(prefix="/public")
public_router.include_router(auth_router)


api_router.include_router(public_router)