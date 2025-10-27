from typing import List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    PROJECT_NAME: str
    BACKEND_CORS_ORIGINS: Optional[List[str]] = ["*"]

    DATABASE_NAME: str
    DATABASE_URL: str

    JWT_SECRET_KEY: str
    PASSWORDS_SALT_SECRET_KEY: str

    class Config:
        case_sensitive = True
        env_file = ".env"


config = Config()