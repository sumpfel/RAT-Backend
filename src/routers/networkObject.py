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
    def get_all_networkObjects(self, current_user: models.DBUser = Depends(get_current_user)):
        # TODO: Only return NetworkObjects that user is allowed to see
        # NOPermissions hat int zahl permissions = enum
        # bei 0 oder keiner NOPermission: nicht zurückgeben

        return self.db.query(models.DBNetworkObject).all()

    @router.post("/", response_model=NetworkObjectOut, status_code=201)
    def create_networkObject(self, nO: NetworkObjectIn):
        db_nO = models.DBNetworkObject(**nO.model_dump()) # AI: How to automatically convert nO to DBNetworkObject
        self.db.add(db_nO)
        self.db.commit()
        self.db.refresh(db_nO)
        return db_nO

    @router.put("/{id}", status_code=201)
    def edit_networkObject(self, id:int, nO: NetworkObjectIn):
        db_nO = self.get_or_404(self.db, models.DBNetworkObject, id)

        for key, value in nO.model_dump().items(): # AI: How to automatically update DBNetworkObject with data from n0
            setattr(db_nO, key, value)

        self.db.refresh(db_nO)
        self.db.commit()

        raise HTTPException(status_code=status.HTTP_200_OK, detail="NetworkObject updated")

    @router.delete("/{id}")
    def delete_item(self, id:int, nO: NetworkObjectIn):
        db_nO = self.get_or_404(self.db, models.DBNetworkObject, id)
        self.db.delete(db_nO)
        self.db.commit()

        raise HTTPException(status_code=status.HTTP_200_OK, detail="NetworkObject deleted")