from fastapi import APIRouter
from api.private.profile import profile_router


private_router = APIRouter(prefix="/private")

private_router.include_router(profile_router)
