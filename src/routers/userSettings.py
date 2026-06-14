from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_restful.cbv import cbv
from pip._internal.commands import show
from pydantic import BaseModel, Field, field_validator, ValidationError
from sqlalchemy.orm import Session
from database import get_db
import models
from models import DBUser
from routers.base import BaseAPI
from auth import Token, get_current_user, verify_password, create_access_token

router = APIRouter(prefix="/user/settings", tags=["UserSettings"], dependencies=[Depends(get_current_user)])

class UserSettingsBase(BaseModel):
    zoom : int = Field(...)
    show_ports : bool = Field(...)
    show_interfaces : bool = Field(...)


class UserSettingsIn(UserSettingsBase):
    pass


class UserSettingsOut(UserSettingsBase):
    model_config = {"from_attributes": True}

@cbv(router)
class UserAPI(BaseAPI):
    db: Session = Depends(get_db)

    @router.get("/", response_model=UserSettingsOut)
    def get_all_userSettings(self, current_user: DBUser = Depends(get_current_user)):
        return self.get_or_404(self.db,models.DBUserSettings,current_user.user_settings_id)

    @router.post("/", status_code=200)
    def update_userSettings(self, userSettings:UserSettingsIn, current_user: DBUser = Depends(get_current_user)):
        db_uS = self.get_or_404(self.db,models.DBUserSettings,current_user.user_settings_id)
        db_uS.zoom = userSettings.zoom
        db_uS.show_ports = userSettings.show_ports
        db_uS.show_interfaces = userSettings.show_interfaces
        self.db.refresh(db_uS)
        self.db.commit()
        return HTTPException(status_code=200)