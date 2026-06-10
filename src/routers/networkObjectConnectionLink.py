import json

from fastapi import APIRouter
from fastapi.params import Depends
from fastapi_restful.cbv import cbv
from pydantic import BaseModel, Field, field_validator, ValidationError
from sqlalchemy import null
from sqlalchemy.orm import Session

from database import get_db
import models
from routers.base import BaseAPI

router = APIRouter(prefix="/networkObjectConnectionLink", tags = ["networkObjectConnectionLink"])

class networkObjectConnectionLinkBase(BaseModel):
    network_object_id : int = Field(..., ge=0)
    network_object_connection_id : int = Field(..., ge=0)

class networkObjectConnectionLinkID(BaseModel):
    id: int = Field(..., ge=0)

class networkObjectConnectionLinkCreate(networkObjectConnectionLinkBase):
    pass

class networkObjectConnectionLinkEdit(networkObjectConnectionLinkBase, networkObjectConnectionLinkID):
    pass

class networkObjectConnectionLinkResponse(networkObjectConnectionLinkEdit):
    model_config = {"from_attributes": True}



@cbv(router)
class networkObjectAPI(BaseAPI):
    db: Session = Depends(get_db)

    @router.get("/", response_model=list[networkObjectConnectionLinkResponse])
    def get_all_networkObjectConnectionLinks(self):
        return self.db.query(models.DBNetworkObjectConnectionLink).all()

    @router.get("/{nO_id}", response_model=list[networkObjectConnectionLinkResponse])
    def get_all_networkObjectConnectionLinks_of_nO(self, nO_id:int):
        return self.db.query(models.DBNetworkObjectConnectionLink).filter(models.DBNetworkObjectConnectionLink.network_object_id==nO_id).all()

    @router.post("/", response_model=networkObjectConnectionLinkResponse, status_code=201)
    def create_networkObjectConnectionLink(self, nOCL: networkObjectConnectionLinkCreate):
        db_nOCL = models.DBNetworkObjectConnectionLink(network_object_id=nOCL.network_object_id, network_object_connection_id=nOCL.network_object_connection_id)
        self.db.add(db_nOCL)
        self.db.commit()
        self.db.refresh(db_nOCL)
        return db_nOCL

    @router.delete("/")
    def delete_item(self, nOCL_id: networkObjectConnectionLinkID):
        db_nOCL = self.get_or_404(self.db, models.DBNetworkObjectConnectionLink, nOCL_id.id)
        self.db.delete(db_nOCL)
        self.db.commit()
        return {"message": f"Network Object with ID {nOCL_id.id} has been vaporised."}