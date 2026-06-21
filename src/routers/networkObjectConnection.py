import json

from fastapi import APIRouter, HTTPException, Query  # KI Claude <KI-17>
from fastapi.params import Depends
from fastapi_restful.cbv import cbv
from pydantic import BaseModel, Field, field_validator, ValidationError
from sqlalchemy import null
from sqlalchemy.orm import Session
from starlette import status

from auth import get_current_user
from database import get_db
import models
from models import DBUser
import permissions  # KI Claude <KI-4>
from routers.base import BaseAPI

router = APIRouter(prefix="/networkObjectConnection", tags = ["networkObjectConnection"], dependencies=[Depends(get_current_user)])

class NetworkObjectConnectionBase(BaseModel):
    name: str = Field(...)
    speed: int = Field(...)
    type: str = Field(...)
    note: str = Field(...)

class NetworkObjectConnectionIn(NetworkObjectConnectionBase):
    pass

class NetworkObjectConnectionInNOID(NetworkObjectConnectionBase):
    nO1: int = Field(...) #ID of interface1
    nO2: int = Field(...) #ID of interface2

class NetworkObjectConnectionOut(NetworkObjectConnectionBase):
    id: int = Field(...)

    model_config = {"from_attributes": True}

@cbv(router)
class networkObjectAPI(BaseAPI):
    db: Session = Depends(get_db)

    def require_edit_on_interface(self, interface_id: int, current_user: DBUser):
        # KI Claude <KI-4>
        # An interface belongs to a NetworkObject; editing a connection on it
        # requires Edit (>= 2) on that NetworkObject.
        db_iface = self.get_or_404(self.db, models.DBNetworkObjectInterface, interface_id)
        permissions.require_permission(self.db, current_user, db_iface.network_object_id, permissions.EDIT)
        return db_iface
        # KI END <KI-4>

    @router.get("/", response_model=list[NetworkObjectConnectionOut])
    def get_all_networkObjectConnections(
        self,
        current_user: DBUser = Depends(get_current_user),
        # KI Claude <KI-17>: optional filtering / sorting / pagination (defaults keep old callers working)
        name: str | None = Query(None, description="Case-insensitive substring search on the connection name"),
        type: str | None = Query(None, description="Filter by exact cable type"),
        min_speed: int | None = Query(None, ge=0, description="Only connections with at least this speed"),
        sort_by: str = Query("id", description="Sort field: id, name, speed or type"),
        order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order: asc or desc"),
        limit: int = Query(200, ge=1, le=1000, description="Pagination: max rows to return"),
        offset: int = Query(0, ge=0, description="Pagination: rows to skip"),
        # KI END <KI-17>
    ):
        # KI Claude <KI-4>
        # Only return connections that touch an interface of a NetworkObject the
        # user may see (See >= 1).
        query = self.db.query(models.DBNetworkObjectConnection)
        if not current_user.is_admin:
            visible_no_ids = self.db.query(models.DBNetworkObjectPermission.network_object_id).filter(
                models.DBNetworkObjectPermission.user_id == current_user.id,
                models.DBNetworkObjectPermission.permissions >= permissions.SEE,
            )
            visible_conn_ids = self.db.query(models.DBNetworkObjectInterface.network_object_connection_id).filter(
                models.DBNetworkObjectInterface.network_object_id.in_(visible_no_ids),
                models.DBNetworkObjectInterface.network_object_connection_id.isnot(None),
            )
            query = query.filter(models.DBNetworkObjectConnection.id.in_(visible_conn_ids))
        # KI END <KI-4>

        # KI Claude <KI-17>: filtering (bound parameters) + sorting (whitelisted) + pagination
        if name:
            query = query.filter(models.DBNetworkObjectConnection.name.ilike(f"%{name}%"))
        if type:
            query = query.filter(models.DBNetworkObjectConnection.type == type)
        if min_speed is not None:
            query = query.filter(models.DBNetworkObjectConnection.speed >= min_speed)

        sort_columns = {
            "id": models.DBNetworkObjectConnection.id,
            "name": models.DBNetworkObjectConnection.name,
            "speed": models.DBNetworkObjectConnection.speed,
            "type": models.DBNetworkObjectConnection.type,
        }
        sort_col = sort_columns.get(sort_by, models.DBNetworkObjectConnection.id)
        query = query.order_by(sort_col.desc() if order == "desc" else sort_col.asc())

        return query.offset(offset).limit(limit).all()
        # KI END <KI-17>

    @router.post("/", response_model=NetworkObjectConnectionOut, status_code=201)
    def create_networkObjectConnection(self, nOC: NetworkObjectConnectionInNOID, current_user: DBUser = Depends(get_current_user)):
        # KI Claude <KI-4>: need Edit on the NetworkObjects of BOTH endpoint interfaces
        self.require_edit_on_interface(nOC.nO1, current_user)
        self.require_edit_on_interface(nOC.nO2, current_user)
        # KI END <KI-4>
        # KI Claude detected problem why/what: NetworkObjectConnectionInNOID carries
        # nO1/nO2 which are NOT columns of DBNetworkObjectConnection. The original
        # `**nOC.model_dump()` would crash. Strip them before building the model.
        conn_data = nOC.model_dump(exclude={"nO1", "nO2"})  # KI Claude <KI-4>
        db_nOC = models.DBNetworkObjectConnection(**conn_data)
        self.db.add(db_nOC)
        self.db.commit()
        self.db.refresh(db_nOC)
        db_NO1 = self.get_or_404(self.db,models.DBNetworkObjectInterface,nOC.nO1)
        db_NO1.network_object_connection_id = db_nOC.id

        db_NO2 = self.get_or_404(self.db,models.DBNetworkObjectInterface,nOC.nO2)
        db_NO2.network_object_connection_id = db_nOC.id
        self.db.commit()
        return db_nOC

    def require_edit_on_connection(self, connection_id: int, current_user: DBUser):
        # KI Claude <KI-4>
        # Editing/deleting an existing connection requires Edit (>= 2) on the
        # NetworkObject of every interface attached to it.
        ifaces = self.db.query(models.DBNetworkObjectInterface).filter(
            models.DBNetworkObjectInterface.network_object_connection_id == connection_id
        ).all()
        for iface in ifaces:
            permissions.require_permission(self.db, current_user, iface.network_object_id, permissions.EDIT)
        # KI END <KI-4>

    @router.put("/{id}", status_code=200)  # KI Claude <KI-19>: an update returns 200, not 201
    def edit_networkObject(self, id:int, nOC: NetworkObjectConnectionIn, current_user: DBUser = Depends(get_current_user)):
        db_nOC = self.get_or_404(self.db,models.DBNetworkObjectConnection, id)
        # KI Claude <KI-4>
        self.require_edit_on_connection(id, current_user)
        # KI END <KI-4>

        for key, value in nOC.model_dump().items():  # AI: How to automatically update DBNetworkObject with data from n0
            setattr(db_nOC, key, value)

        # KI Claude detected problem why/what: refresh() before commit() discarded the edits.
        self.db.commit()  # KI Claude <KI-9>
        self.db.refresh(db_nOC)
        # KI Claude <KI-19>: success returns a normal 200 body, not a raised HTTPException
        return {"detail": "NetworkObjectConnection updated"}

    @router.delete("/{id}")
    def delete_item(self, id:int, current_user: DBUser = Depends(get_current_user)):
        # KI Claude detected problem why/what: original used DBNetworkObject instead of
        # DBNetworkObjectConnection here, so it deleted the wrong table's row (or 404'd
        # on a valid connection id). Fixed to DBNetworkObjectConnection.
        db_nOC = self.get_or_404(self.db, models.DBNetworkObjectConnection, id)  # KI Claude <KI-4>
        # KI Claude <KI-4>: deleting a connection needs Edit on both endpoints
        self.require_edit_on_connection(id, current_user)
        # KI END <KI-4>
        self.db.delete(db_nOC)
        self.db.commit()
        # KI Claude <KI-19>: success returns a normal 200 body, not a raised HTTPException
        return {"detail": "NetworkObjectConnection deleted"}