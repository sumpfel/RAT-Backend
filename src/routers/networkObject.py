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

router = APIRouter(prefix="/networkObject", tags = ["networkObject"])

class networkObjectBase(BaseModel):
    json_data : str = Field(...)

class networkObjectID(BaseModel):
    id: int = Field(..., ge=0)

class networkObjectCreate(networkObjectBase):
    @field_validator("json_data")
    @classmethod
    def check_password_complexity(cls, json_str: str) -> str:
        #json_str = json_str.strip()
        try:
            json.loads(json_str)
        except:
            raise ValidationError("string not json")

class networkObjectEdit(networkObjectBase, networkObjectID):
    pass

class networkObjectResponse(networkObjectEdit):
    model_config = {"from_attributes": True}



@cbv(router)
class networkObjectAPI(BaseAPI):
    db: Session = Depends(get_db)

    @router.get("/", response_model=list[networkObjectResponse])
    def get_all_networkObjects(self):
        return self.db.query(models.DBNetworkObject).all()

    @router.post("/", response_model=networkObjectResponse, status_code=201)
    def create_networkObject(self, nO: networkObjectCreate):
        db_nO = models.DBNetworkObject(json_data = nO.json_data)
        self.db.add(db_nO)
        self.db.commit()
        self.db.refresh(db_nO)
        return db_nO

    @router.put("/", status_code=201)
    def edit_networkObject(self,nO: networkObjectEdit):
        db_nO = self.get_or_404(self.db,models.DBNetworkObject, nO.id)
        db_nO.json_data = nO.json_data
        self.db.refresh(db_nO)
        self.db.commit()
        return {"message": f"Network Object with ID {nO.id} has been updated."}

    @router.delete("/")
    def delete_item(self, nO_id: networkObjectID):
        db_nO = self.get_or_404(self.db, models.DBNetworkObject, nO_id.id)
        self.db.delete(db_nO)
        self.db.commit()
        return {"message": f"Network Object with ID {nO_id.id} has been vaporised."}