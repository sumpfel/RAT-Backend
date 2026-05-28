from fastapi import APIRouter
from fastapi.params import Depends
from fastapi_restful.cbv import cbv
from pydantic import BaseModel, Field, field_validator, ValidationError
from sqlalchemy.orm import Session

from database import get_db
import models
from routers.base import BaseAPI

router = APIRouter(prefix="/user", tags=["User"])

# TODO: If there are no users, create admin user

class UserBase(BaseModel):
    username: str = Field(...)
    password: str = Field(...)
    privileges: int = Field(default=0)

class UserCreate(UserBase):
    @field_validator("password")
    @classmethod
    def check_password_complexity(cls, password: str) -> str:
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")

        # Source - https://stackoverflow.com/a/57062899
        # Posted by ipaleka
        # Retrieved 2026-05-28, License - CC BY-SA 4.0

        if not any(not c.isalnum() for c in password):
            raise ValidationError("Password must contain at least one special character")

        if not any(not c.islower() for c in password):
            raise ValidationError("Password must contain at least one uppercase letter")

        return password