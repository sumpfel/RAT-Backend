from fastapi import APIRouter, HTTPException, Query  # KI Claude <KI-17>
from fastapi.params import Depends
from fastapi_restful.cbv import cbv
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status

from auth import get_current_user
from database import get_db
import models
from models import DBUser
import permissions  # KI Claude <KI-3>
from routers.base import BaseAPI

router = APIRouter(prefix="/networkObjectInterface", tags=["networkObjectInterface"], dependencies=[Depends(get_current_user)])

class NetworkObjectInterfaceBase(BaseModel):
    network_object_id: int = Field(...)
    # KI Claude <KI-10> detected problem why/what: this column is NULL for any interface
    # that is not attached to a connection, but it was typed as a non-optional `int`. The
    # GET list endpoint then crashed with a ResponseValidationError (None is not an int),
    # which blocked the C# client from loading the topology. Made it Optional[int].
    network_object_connection_id: int | None = Field(None)
    name: str = Field(...)
    max_speed: int = Field(...)
    is_up: bool = Field(...)
    ipv4: str = Field(...)
    ipv6: str = Field(...)
    ipv4_subnet_mask: str = Field(...)
    ipv6_prefix_length: int = Field(...)
    ipv4_gateway: str = Field(...)

class NetworkObjectInterfaceIn(NetworkObjectInterfaceBase):
    pass

class NetworkObjectInterfaceOut(NetworkObjectInterfaceBase):
    id: int = Field(..., ge=0)

    model_config = {"from_attributes": True}

@cbv(router)
class NetworkObjectInterfaceAPI(BaseAPI):
    db: Session = Depends(get_db)

    @router.get("/", response_model=list[NetworkObjectInterfaceOut])
    def get_all_networkObjectInterfaces(
        self,
        current_user: DBUser = Depends(get_current_user),
        # KI Claude <KI-17>: optional filtering / pagination (defaults keep old callers working)
        network_object_id: int | None = Query(None, description="Only interfaces of this NetworkObject"),
        name: str | None = Query(None, description="Case-insensitive substring search on the interface name"),
        is_up: bool | None = Query(None, description="Filter by link state (interface up/down)"),
        limit: int = Query(200, ge=1, le=1000, description="Pagination: max rows to return"),
        offset: int = Query(0, ge=0, description="Pagination: rows to skip"),
        # KI END <KI-17>
    ):
        # KI Claude <KI-3>
        # Only return interfaces that belong to NetworkObjects the user may see (See >= 1).
        query = self.db.query(models.DBNetworkObjectInterface)
        if not current_user.is_admin:
            visible_ids = self.db.query(models.DBNetworkObjectPermission.network_object_id).filter(
                models.DBNetworkObjectPermission.user_id == current_user.id,
                models.DBNetworkObjectPermission.permissions >= permissions.SEE,
            )
            query = query.filter(models.DBNetworkObjectInterface.network_object_id.in_(visible_ids))
        # KI END <KI-3>

        # KI Claude <KI-17>: filtering (bound parameters) + pagination
        if network_object_id is not None:
            query = query.filter(models.DBNetworkObjectInterface.network_object_id == network_object_id)
        if name:
            query = query.filter(models.DBNetworkObjectInterface.name.ilike(f"%{name}%"))
        if is_up is not None:
            query = query.filter(models.DBNetworkObjectInterface.is_up == is_up)

        return query.order_by(models.DBNetworkObjectInterface.id.asc()).offset(offset).limit(limit).all()
        # KI END <KI-17>

    @router.post("/", response_model=NetworkObjectInterfaceOut, status_code=201)
    def create_networkObjectInterface(self, nOI: NetworkObjectInterfaceIn, current_user: DBUser = Depends(get_current_user)):
        # KI Claude <KI-3>: adding an interface needs Edit (>= 2) on the target NetworkObject
        permissions.require_permission(self.db, current_user, nOI.network_object_id, permissions.EDIT)
        # KI END <KI-3>
        db_nOI = models.DBNetworkObjectInterface(**nOI.model_dump())
        self.db.add(db_nOI)
        self.db.commit()
        self.db.refresh(db_nOI)
        return db_nOI

    @router.put("/{id}", status_code=200)  # KI Claude <KI-19>: an update returns 200, not 201
    def edit_networkObjectInterface(self, id: int, nOI: NetworkObjectInterfaceIn, current_user: DBUser = Depends(get_current_user)):
        db_nOI = self.get_or_404(self.db, models.DBNetworkObjectInterface, id)
        # KI Claude <KI-3>: need Edit on the interface's current NetworkObject AND on the target one
        permissions.require_permission(self.db, current_user, db_nOI.network_object_id, permissions.EDIT)
        permissions.require_permission(self.db, current_user, nOI.network_object_id, permissions.EDIT)
        # KI END <KI-3>

        for key, value in nOI.model_dump().items(): # AI: How to automatically update DBNetworkObject with data from n0
            setattr(db_nOI, key, value)

        # KI Claude detected problem why/what: refresh() before commit() discarded the edits.
        self.db.commit()  # KI Claude <KI-9>
        self.db.refresh(db_nOI)

        # KI Claude <KI-19>: success returns a normal 200 body, not a raised HTTPException
        return {"detail": "NetworkObjectInterface updated"}

    @router.delete("/{id}")
    def delete_networkObjectInterface(self, id: int, current_user: DBUser = Depends(get_current_user)):
        db_nOI = self.get_or_404(self.db, models.DBNetworkObjectInterface, id)
        # KI Claude <KI-3>: deleting an interface needs Edit (>= 2) on its NetworkObject
        permissions.require_permission(self.db, current_user, db_nOI.network_object_id, permissions.EDIT)
        # KI END <KI-3>
        self.db.delete(db_nOI)
        self.db.commit()

        # KI Claude <KI-19>: success returns a normal 200 body, not a raised HTTPException
        return {"detail": "NetworkObjectInterface deleted"}
