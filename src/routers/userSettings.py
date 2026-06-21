from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_restful.cbv import cbv
# KI Claude detected problem why/what: stray `from pip._internal.commands import show`
# import has no use and pulls in pip internals; removed.
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


# KI Claude <KI-6>
# The DB columns are camelCase (showPorts/showInterfaces) while the API uses
# snake_case. Map them via validation aliases so `from_attributes` can read the
# ORM object, while the JSON response still uses the snake_case field names.
class UserSettingsOut(BaseModel):
    zoom: int = Field(...)
    show_ports: bool = Field(..., validation_alias="showPorts")
    show_interfaces: bool = Field(..., validation_alias="showInterfaces")

    model_config = {"from_attributes": True, "populate_by_name": True}
# KI END <KI-6>

@cbv(router)
class UserAPI(BaseAPI):
    db: Session = Depends(get_db)

    # KI Claude <KI-6>
    # Settings are linked via DBUserSettings.user_id, not a user_settings_id column
    # on the user. Look them up by the current user's id; create them lazily if a
    # legacy user has none yet.
    def get_or_create_settings(self, current_user: DBUser):
        db_uS = self.db.query(models.DBUserSettings).filter(
            models.DBUserSettings.user_id == current_user.id
        ).first()
        if db_uS is None:
            db_uS = models.DBUserSettings(user_id=current_user.id)
            self.db.add(db_uS)
            self.db.commit()
            self.db.refresh(db_uS)
        return db_uS
    # KI END <KI-6>

    @router.get("/", response_model=UserSettingsOut)
    def get_all_userSettings(self, current_user: DBUser = Depends(get_current_user)):
        return self.get_or_create_settings(current_user)  # KI Claude <KI-6>

    @router.put("/", status_code=200)
    def update_userSettings(self, userSettings:UserSettingsIn, current_user: DBUser = Depends(get_current_user)):
        db_uS = self.get_or_create_settings(current_user)  # KI Claude <KI-6>
        db_uS.zoom = userSettings.zoom
        db_uS.showPorts = userSettings.show_ports
        db_uS.showInterfaces = userSettings.show_interfaces
        self.db.commit()  # KI Claude detected problem why/what: refresh() before commit discarded the edits; commit first
        self.db.refresh(db_uS)
        # KI Claude <KI-19>: success returns a normal 200 body, not a raised HTTPException
        return {"detail": "UserSettings updated"}