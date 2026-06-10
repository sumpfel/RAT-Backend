from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_restful.cbv import cbv
from pydantic import BaseModel, Field, field_validator, ValidationError
from sqlalchemy.orm import Session
from database import get_db
import models
from models import DBUser
from routers.base import BaseAPI
from auth import Token, get_current_user, verify_password, create_access_token

router = APIRouter(prefix="/user", tags=["User"])

# TODO: If there are no users, create admin user


class UserBase(BaseModel):
    username: str = Field(...)

class UserIn(UserBase):
    hashed_password: str = Field(...)

class UserOut(UserBase):
    privileges: int = Field(default=0)

@cbv(router)
class UserAPI(BaseAPI):

    db: Session= Depends(get_db)

    @router.post("/login", response_model=Token)
    def login(self, form: OAuth2PasswordRequestForm = Depends()):
        user = self.db.query(DBUser).filter(DBUser.username == form.username).first()
        
        if not user or not verify_password(form.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        token = create_access_token({"sub": user.username})

        return {"access_token": token, "token_type": "bearer"}

    @router.get("/me", response_model=UserOut)
    def get_me(self, current_user: DBUser = Depends(get_current_user)):
        return current_user