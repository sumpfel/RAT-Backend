from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi_restful.cbv import cbv
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status

from auth import get_current_user
from database import get_db
import models
from models import DBUser
from routers.base import BaseAPI

router = APIRouter(prefix="/login", tags=["login"], dependencies=[Depends(get_current_user)])

class LoginBase(BaseModel):
    network_object_permission_id: int = Field(...)
    port: int = Field(...)
    type: str = Field(...)
    username: str = Field(...)
    password: str = Field(...)

class LoginIn(LoginBase):
    pass

class LoginOut(LoginBase):
    id: int = Field(..., ge=0)

    model_config = {"from_attributes": True}

@cbv(router)
class LoginAPI(BaseAPI):
    db: Session = Depends(get_db)

    def check_permission_owner(self, network_object_permission_id: int, current_user: DBUser):
        db_nOP = self.get_or_404(self.db, models.DBNetworkObjectPermission, network_object_permission_id)
        if db_nOP.user_id != current_user.id:
            raise HTTPException(status_code=403)
        return db_nOP

    @router.get("/", response_model=list[LoginOut])
    def get_all_logins(self, current_user: DBUser = Depends(get_current_user)):
        # KI Claude
        return self.db.query(models.DBLogin).join(
            models.DBNetworkObjectPermission,
            models.DBLogin.network_object_permission_id == models.DBNetworkObjectPermission.id
        ).filter(models.DBNetworkObjectPermission.user_id == current_user.id).all()
        # KI END

    @router.post("/", response_model=LoginOut, status_code=201)
    def create_login(self, login: LoginIn, current_user: DBUser = Depends(get_current_user)):
        self.check_permission_owner(login.network_object_permission_id, current_user)
        db_login = models.DBLogin(**login.model_dump())
        self.db.add(db_login)
        self.db.commit()
        self.db.refresh(db_login)
        return db_login

    @router.put("/{id}", status_code=200)  # KI Claude <KI-19>: an update returns 200, not 201
    def edit_login(self, id: int, login: LoginIn, current_user: DBUser = Depends(get_current_user)):
        db_login = self.get_or_404(self.db, models.DBLogin, id)
        self.check_permission_owner(db_login.network_object_permission_id, current_user)
        self.check_permission_owner(login.network_object_permission_id, current_user)
        
        
        for key, value in login.model_dump().items(): # AI: How to automatically update DBNetworkObject with data from n0
            setattr(db_login, key, value)

        # KI Claude detected problem why/what: refresh() before commit() discarded the edits.
        self.db.commit()  # KI Claude <KI-9>
        self.db.refresh(db_login)

        # KI Claude <KI-19>: success returns a normal 200 body, not a raised HTTPException
        return {"detail": "Login updated"}

    @router.delete("/{id}")
    def delete_login(self, id: int, current_user: DBUser = Depends(get_current_user)):
        db_login = self.get_or_404(self.db, models.DBLogin, id)
        self.check_permission_owner(db_login.network_object_permission_id, current_user)

        self.db.delete(db_login)
        self.db.commit()

        # KI Claude <KI-19>: success returns a normal 200 body, not a raised HTTPException
        return {"detail": "Login deleted"}
