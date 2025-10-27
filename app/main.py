from datetime import time
import os
from asyncio import run
from beanie import init_beanie
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.models import User
from app.core.database import db
from app.core.config import config
from api.api_router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_beanie(
        database=db,
        document_models=[
            User
        ],
    )

    yield


def get_application():
    _app = FastAPI(title=config.PROJECT_NAME, lifespan=lifespan)

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return _app


app = get_application()

# health check
@app.get("/health")
async def health():   
    return {"status": "ok"}
    
app.include_router(api_router)