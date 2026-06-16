import json

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi_restful.cbv import cbv
from pydantic import BaseModel, Field, field_validator, ValidationError
from sqlalchemy import null
from sqlalchemy.orm import Session
from sqlalchemy.testing.pickleable import User
from starlette import status

from auth import get_current_user
from database import get_db
import models
from models import DBUser
import permissions  # KI Claude <KI-2>
from routers.base import BaseAPI

router = APIRouter(prefix="/networkObject", tags = ["networkObject"], dependencies=[Depends(get_current_user)])

class NetworkObjectBase(BaseModel):
    name: str = Field(...)
    type: str = Field(...)
    x: int = Field(...)
    y: int = Field(...)
    os: str = Field(...)
    cpu: str = Field(...)
    gpu: str = Field(...)
    ram: str = Field(...)
    specs: str = Field(...)

class NetworkObjectIn(NetworkObjectBase):
    pass

class NetworkObjectOut(NetworkObjectBase):
    id: int = Field(..., ge=0)

    model_config = {"from_attributes": True}

@cbv(router)
class NetworkObjectAPI(BaseAPI):
    db: Session = Depends(get_db)

    @router.get("/", response_model=list[NetworkObjectOut])
    def get_all_networkObjects(self, current_user: DBUser = Depends(get_current_user)):
        # KI Claude <KI-2>
        # Only return NetworkObjects the user may see (See >= 1).
        # No permission row or permission 0 == Hidden -> excluded.
        # Global admins see everything.
        if current_user.is_admin:
            return self.db.query(models.DBNetworkObject).all()

        visible_ids = self.db.query(models.DBNetworkObjectPermission.network_object_id).filter(
            models.DBNetworkObjectPermission.user_id == current_user.id,
            models.DBNetworkObjectPermission.permissions >= permissions.SEE,
        )
        return self.db.query(models.DBNetworkObject).filter(
            models.DBNetworkObject.id.in_(visible_ids)
        ).all()
        # KI END <KI-2>

    @router.post("/", response_model=NetworkObjectOut, status_code=201)
    def create_networkObject(self, nO: NetworkObjectIn, current_user: DBUser = Depends(get_current_user)):
        # KI Claude <KI-2>
        # Only users with the canCreate flag (or admins) may create objects.
        if not (current_user.is_admin or current_user.canCreate):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to create NetworkObjects",
            )
        # KI END <KI-2>
        db_nO = models.DBNetworkObject(**nO.model_dump()) # AI: How to automatically convert nO to DBNetworkObject
        self.db.add(db_nO)
        self.db.commit()
        self.db.refresh(db_nO)

        # KI Claude <KI-2>
        # The creator becomes Owner, otherwise nobody (not even the creator)
        # could see the freshly created object.
        owner_perm = models.DBNetworkObjectPermission(
            user_id=current_user.id,
            network_object_id=db_nO.id,
            permissions=permissions.OWNER,
        )
        self.db.add(owner_perm)
        self.db.commit()
        # KI END <KI-2>
        return db_nO

    @router.put("/{id}", status_code=201)
    def edit_networkObject(self, id:int, nO: NetworkObjectIn, current_user: DBUser = Depends(get_current_user)):
        # KI Claude <KI-2>: editing settings (name etc) needs Edit (>= 2)
        permissions.require_permission(self.db, current_user, id, permissions.EDIT)
        # KI END <KI-2>
        db_nO = self.get_or_404(self.db, models.DBNetworkObject, id)

        for key, value in nO.model_dump().items(): # AI: How to automatically update DBNetworkObject with data from n0
            setattr(db_nO, key, value)

        # KI Claude detected problem why/what: refresh() before commit() reloaded the
        # row from the DB and discarded the edits. Commit first, then refresh.
        self.db.commit()  # KI Claude <KI-9>
        self.db.refresh(db_nO)

        raise HTTPException(status_code=status.HTTP_200_OK, detail="NetworkObject updated")

    @router.delete("/{id}")
    def delete_item(self, id:int, current_user: DBUser = Depends(get_current_user)):
        # KI Claude <KI-2>: only the Owner (4) may delete the object
        permissions.require_permission(self.db, current_user, id, permissions.OWNER)
        # KI END <KI-2>
        db_nO = self.get_or_404(self.db, models.DBNetworkObject, id)

        # KI Claude <KI-11> detected problem why/what: deleting a NetworkObject only removed its
        # permission rows, leaving its interfaces (and the connections / logins / snmp settings hanging
        # off them) as dangling rows. On the next graph load the C# client then references interfaces
        # whose object is gone. Cascade-delete everything that belongs to this object.
        ifaces = self.db.query(models.DBNetworkObjectInterface).filter(
            models.DBNetworkObjectInterface.network_object_id == id
        ).all()
        connection_ids = {i.network_object_connection_id for i in ifaces if i.network_object_connection_id}
        for iface in ifaces:
            self.db.delete(iface)
        # delete the connections those interfaces used (the other endpoint's FK is cleared on object delete too)
        for conn_id in connection_ids:
            conn = self.db.query(models.DBNetworkObjectConnection).filter(
                models.DBNetworkObjectConnection.id == conn_id
            ).first()
            if conn:
                self.db.delete(conn)
        # logins + snmp settings hang off the permission rows -> remove them before the permission rows
        perm_ids = [p.id for p in self.db.query(models.DBNetworkObjectPermission).filter(
            models.DBNetworkObjectPermission.network_object_id == id
        ).all()]
        if perm_ids:
            self.db.query(models.DBLogin).filter(
                models.DBLogin.network_object_permission_id.in_(perm_ids)
            ).delete(synchronize_session=False)
            self.db.query(models.DBSNMPSettings).filter(
                models.DBSNMPSettings.network_object_permission_id.in_(perm_ids)
            ).delete(synchronize_session=False)
        # KI END <KI-11>

        # KI Claude <KI-2>: clean up permission rows so they don't dangle
        self.db.query(models.DBNetworkObjectPermission).filter(
            models.DBNetworkObjectPermission.network_object_id == id
        ).delete()
        # KI END <KI-2>

        self.db.delete(db_nO)
        self.db.commit()

        raise HTTPException(status_code=status.HTTP_200_OK, detail="NetworkObject deleted")