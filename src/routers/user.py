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
from auth import Token, get_current_user, verify_password, create_access_token, hash_password  # KI Claude <KI-7>

router = APIRouter(prefix="/user", tags=["User"])


class UserBase(BaseModel):
    username: str = Field(...)
    is_admin: bool = Field(default=0)

class UserIn(UserBase):
    # KI Claude detected problem why/what: field was named `hashed_password` but the
    # value is a plaintext password (the login compares plaintext too). Renamed to
    # `password`; it is hashed server-side in register().
    password: str = Field(...)  # KI Claude <KI-7>

class UserOut(UserBase):
    id: int = Field(...)

    model_config = {"from_attributes": True}

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

    @router.post("/register", response_model=UserOut)
    def register(self, user: UserIn):
        # KI Claude <KI-7>
        # Create the user with a hashed password and give every new user their own
        # UserSettings row (defaults come from the model).
        existing = self.db.query(DBUser).filter(DBUser.username == user.username).first()
        if existing:
            raise HTTPException(status_code=409, detail="Username already exists")

        db_user = DBUser(
            username=user.username,
            password=hash_password(user.password),
            is_admin=user.is_admin,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        db_settings = models.DBUserSettings(user_id=db_user.id)
        self.db.add(db_settings)
        self.db.commit()

        return db_user
        # KI END <KI-7>