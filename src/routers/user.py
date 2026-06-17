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
    # KI Claude <KI-10>: expose canCreate so the C# client knows whether a user may
    # create NetworkObjects (RAT_Data.User.CanCreate / NetworkUser.CanCreate).
    can_create: bool = Field(default=False, validation_alias="canCreate")

    model_config = {"populate_by_name": True}  # KI Claude <KI-10>

class UserIn(UserBase):
    # KI Claude detected problem why/what: field was named `hashed_password` but the
    # value is a plaintext password (the login compares plaintext too). Renamed to
    # `password`; it is hashed server-side in register().
    password: str = Field(...)  # KI Claude <KI-7>

class UserOut(UserBase):
    id: int = Field(...)

    model_config = {"from_attributes": True, "populate_by_name": True}  # KI Claude <KI-10>

# KI Claude <KI-12>
# Edit-user payload. Every field is optional so the same endpoint serves both an admin
# (who may change username / password / is_admin / can_create on anyone) and a normal
# user editing only their own username + password. Admin-only fields are ignored for a
# self-edit by a non-admin (enforced in the route).
class UserEdit(BaseModel):
    username: str | None = Field(default=None)
    password: str | None = Field(default=None)
    is_admin: bool | None = Field(default=None)
    can_create: bool | None = Field(default=None, validation_alias="canCreate")

    model_config = {"populate_by_name": True}
# KI END <KI-12>

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

    # KI Claude <KI-10>
    # List all users. The C# client needs this to resolve the user_id stored in a
    # NetworkObjectPermission back to a username (Access Control tab) and to build
    # its IDatabaseConnection.GetAllUsers(). Only authenticated users may call it.
    @router.get("/", response_model=list[UserOut])
    def get_all_users(self, current_user: DBUser = Depends(get_current_user)):
        return self.db.query(DBUser).all()
    # KI END <KI-10>

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
            canCreate=user.can_create,  # KI Claude <KI-10>
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        db_settings = models.DBUserSettings(user_id=db_user.id)
        self.db.add(db_settings)
        self.db.commit()

        return db_user
        # KI END <KI-7>

    # KI Claude <KI-12>
    # Edit a user. Authorization:
    #   - a global admin may edit ANY user and ANY field (username/password/is_admin/can_create)
    #   - a normal user may edit ONLY themselves, and only username + password
    #     (is_admin / can_create from the payload are ignored for a self-edit by a non-admin)
    @router.put("/{id}", response_model=UserOut)
    def edit_user(self, id: int, edit: UserEdit, current_user: DBUser = Depends(get_current_user)):
        db_user = self.get_or_404(self.db, DBUser, id)

        is_self = current_user.id == db_user.id
        if not current_user.is_admin and not is_self:
            raise HTTPException(status_code=403, detail="You may only edit your own account")

        # username (both admin and self may change it) — keep it unique
        if edit.username is not None and edit.username != db_user.username:
            clash = self.db.query(DBUser).filter(DBUser.username == edit.username).first()
            if clash:
                raise HTTPException(status_code=409, detail="Username already exists")
            db_user.username = edit.username

        # password (both admin and self)
        if edit.password:
            db_user.password = hash_password(edit.password)

        # admin / can_create — only a global admin may change these
        if current_user.is_admin:
            if edit.is_admin is not None:
                db_user.is_admin = edit.is_admin
            if edit.can_create is not None:
                db_user.canCreate = edit.can_create

        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    # KI END <KI-12>