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

router = APIRouter(prefix="/snmpSettings", tags=["snmpSettings"], dependencies=[Depends(get_current_user)])

class SNMPSettingsBase(BaseModel):
    network_object_permission_id: int = Field(...)
    read_community: str = Field(...)
    write_community: str = Field(...)

class SNMPSettingsIn(SNMPSettingsBase):
    pass

class SNMPSettingsOut(SNMPSettingsBase):
    id: int = Field(..., ge=0)

    model_config = {"from_attributes": True}

@cbv(router)
class SNMPSettingsAPI(BaseAPI):
    db: Session = Depends(get_db)

    def check_permission_owner(self, network_object_permission_id: int, current_user: DBUser):
        db_nOP = self.get_or_404(self.db, models.DBNetworkObjectPermission, network_object_permission_id)
        if db_nOP.user_id != current_user.id:
            raise HTTPException(status_code=403)
        return db_nOP

    @router.get("/", response_model=list[SNMPSettingsOut])
    def get_all_snmpSettings(self, current_user: DBUser = Depends(get_current_user)):
        # KI Claude
        return self.db.query(models.DBSNMPSettings).join(
            models.DBNetworkObjectPermission,
            models.DBSNMPSettings.network_object_permission_id == models.DBNetworkObjectPermission.id
        ).filter(models.DBNetworkObjectPermission.user_id == current_user.id).all()
        # KI end

    @router.post("/", response_model=SNMPSettingsOut, status_code=201)
    def create_snmpSettings(self, snmp: SNMPSettingsIn, current_user: DBUser = Depends(get_current_user)):
        self.check_permission_owner(snmp.network_object_permission_id, current_user)
        db_snmp = models.DBSNMPSettings(**snmp.model_dump())
        self.db.add(db_snmp)
        self.db.commit()
        self.db.refresh(db_snmp)
        return db_snmp

    @router.put("/{id}", status_code=201)
    def edit_snmpSettings(self, id: int, snmp: SNMPSettingsIn, current_user: DBUser = Depends(get_current_user)):
        db_snmp = self.get_or_404(self.db, models.DBSNMPSettings, id)
        self.check_permission_owner(db_snmp.network_object_permission_id, current_user)
        self.check_permission_owner(snmp.network_object_permission_id, current_user)

        for key, value in snmp.model_dump().items(): # AI: How to automatically update DBNetworkObject with data from n0
            setattr(db_snmp, key, value)

        # KI Claude detected problem why/what: refresh() before commit() discarded the edits.
        self.db.commit()  # KI Claude <KI-9>
        self.db.refresh(db_snmp)

        raise HTTPException(status_code=status.HTTP_200_OK, detail="SNMPSettings updated")

    @router.delete("/{id}")
    def delete_snmpSettings(self, id: int, current_user: DBUser = Depends(get_current_user)):
        db_snmp = self.get_or_404(self.db, models.DBSNMPSettings, id)
        self.check_permission_owner(db_snmp.network_object_permission_id, current_user)

        self.db.delete(db_snmp)
        self.db.commit()

        raise HTTPException(status_code=status.HTTP_200_OK, detail="SNMPSettings deleted")
