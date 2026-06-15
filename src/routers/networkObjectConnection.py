import json

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi_restful.cbv import cbv
from pydantic import BaseModel, Field, field_validator, ValidationError
from sqlalchemy import null
from sqlalchemy.orm import Session
from starlette import status

from auth import get_current_user
from database import get_db
import models
from routers.base import BaseAPI

router = APIRouter(prefix="/networkObjectConnection", tags = ["networkObjectConnection"], dependencies=[Depends(get_current_user)])

class NetworkObjectConnectionBase(BaseModel):
    name: str = Field(...)
    speed: int = Field(...)
    type: str = Field(...)
    note: str = Field(...)

class NetworkObjectConnectionIn(NetworkObjectConnectionBase):
    pass

class NetworkObjectConnectionOut(NetworkObjectConnectionBase):
    id: int = Field(...)

    model_config = {"from_attributes": True}

@cbv(router)
class networkObjectAPI(BaseAPI):
    db: Session = Depends(get_db)

    @router.get("/", response_model=list[NetworkObjectConnectionOut])
    def get_all_networkObjectConnections(self):
        return self.db.query(models.DBNetworkObjectConnection).all()

    @router.post("/", response_model=NetworkObjectConnectionOut, status_code=201)
    def create_networkObjectConnection(self, nOC: NetworkObjectConnectionIn):
        db_nOC = models.DBNetworkObjectConnection(**nOC.model_dump())
        self.db.add(db_nOC)
        self.db.commit()
        self.db.refresh(db_nOC)
        return db_nOC

    @router.put("/{id}", status_code=201)
    def edit_networkObject(self, id:int, nOC: NetworkObjectConnectionIn):
        db_nOC = self.get_or_404(self.db,models.DBNetworkObjectConnection, id)

        for key, value in nOC.model_dump().items():  # AI: How to automatically update DBNetworkObject with data from n0
            setattr(db_nOC, key, value)

        self.db.refresh(db_nOC)
        self.db.commit()
        raise HTTPException(status_code=status.HTTP_200_OK, detail="NetworkObject updated")

    @router.delete("/{id}")
    def delete_item(self, id:int):
        db_nOC = self.get_or_404(self.db, models.DBNetworkObject, id)
        self.db.delete(db_nOC)
        self.db.commit()
        raise HTTPException(status_code=status.HTTP_200_OK, detail="NetworkObject deleted")