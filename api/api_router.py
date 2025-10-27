from fastapi import APIRouter, Depends
from api.public.auth import auth_router
from api.private import private_router
from app.core.jwt import FastJWT

api_router = APIRouter(prefix="/api")

public_router = APIRouter(prefix="/public")
public_router.include_router(auth_router)


api_router.include_router(public_router)
api_router.include_router(private_router, dependencies=[Depends(FastJWT().login_required)])