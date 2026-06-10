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

router = APIRouter(prefix="/networkObjectConnection", tags = ["networkObjectConnection"])

class networkObjectConnectionBase(BaseModel):
    json_data : str = Field(...)

class networkObjectConnectionID(BaseModel):
    id: int = Field(..., ge=0)

class networkObjectCreate(networkObjectConnectionBase):
    @field_validator("json_data")
    @classmethod
    def check_password_complexity(cls, json_str: str) -> str:
        #json_str = json_str.strip()
        try:
            json.loads(json_str)
        except:
            raise ValidationError("string not json")

class networkObjectConnectionEdit(networkObjectConnectionBase, networkObjectConnectionID):
    pass

class networkObjectConnectionResponse(networkObjectConnectionEdit):
    model_config = {"from_attributes": True}



@cbv(router)
class networkObjectAPI(BaseAPI):
    db: Session = Depends(get_db)

    @router.get("/", response_model=list[networkObjectConnectionResponse])
    def get_all_networkObjectConnections(self):
        return self.db.query(models.DBNetworkObjectConnection).all()

    @router.post("/", response_model=networkObjectConnectionResponse, status_code=201)
    def create_networkObjectConnection(self, nOC: networkObjectCreate):
        db_nOC = models.DBNetworkObjectConnection(json_data = nOC.json_data)
        self.db.add(db_nOC)
        self.db.commit()
        self.db.refresh(db_nOC)
        return db_nOC

    @router.put("/", status_code=201)
    def edit_networkObject(self,nOC: networkObjectConnectionEdit):
        db_nOC = self.get_or_404(self.db,models.DBNetworkObjectConnection, nOC.id)
        db_nOC.json_data = nOC.json_data
        self.db.refresh(db_nOC)
        self.db.commit()
        return {"message": f"Network Object with ID {nOC.id} has been updated."}

    @router.delete("/")
    def delete_item(self, nOC_id: networkObjectConnectionID):
        db_nOC = self.get_or_404(self.db, models.DBNetworkObject, nOC_id.id)
        self.db.delete(db_nOC)
        self.db.commit()
        return {"message": f"Network Object with ID {nOC_id.id} has been vaporised."}