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

router = APIRouter(prefix="/networkObjectPermission", tags=["networkObjectPermission"], dependencies=[Depends(get_current_user)])

class NetworkObjectPermissionBase(BaseModel):
    network_object_id: int = Field(...)
    permissions: int = Field(...)

class NetworkObjectPermissionIn(NetworkObjectPermissionBase):
    pass

class NetworkObjectPermissionOut(NetworkObjectPermissionBase):
    id: int = Field(..., ge=0)
    user_id: int = Field(...)

    model_config = {"from_attributes": True}

@cbv(router)
class NetworkObjectPermissionAPI(BaseAPI):
    db: Session = Depends(get_db)

    @router.get("/", response_model=list[NetworkObjectPermissionOut])
    def get_all_networkObjectPermissions(self, current_user: DBUser = Depends(get_current_user)):
        return self.db.query(models.DBNetworkObjectPermission).filter(
            models.DBNetworkObjectPermission.user_id == current_user.id
        ).all()

    @router.post("/", response_model=NetworkObjectPermissionOut, status_code=201)
    def create_networkObjectPermission(self, nOP: NetworkObjectPermissionIn, current_user: DBUser = Depends(get_current_user)):
        db_nOP = models.DBNetworkObjectPermission(**nOP.model_dump(), user_id=current_user.id)
        self.db.add(db_nOP)
        self.db.commit()
        self.db.refresh(db_nOP)
        return db_nOP

    @router.put("/{id}", status_code=201)
    def edit_networkObjectPermission(self, id: int, nOP: NetworkObjectPermissionIn, current_user: DBUser = Depends(get_current_user)):
        db_nOP = self.get_or_404(self.db, models.DBNetworkObjectPermission, id)

        for key, value in nOP.model_dump().items():
            setattr(db_nOP, key, value)

        self.db.refresh(db_nOP)
        self.db.commit()

        raise HTTPException(status_code=status.HTTP_200_OK, detail="NetworkObjectPermission updated")

    @router.delete("/{id}")
    def delete_networkObjectPermission(self, id: int, current_user: DBUser = Depends(get_current_user)):
        db_nOP = self.get_or_404(self.db, models.DBNetworkObjectPermission, id)

        self.db.delete(db_nOP)
        self.db.commit()

        raise HTTPException(status_code=status.HTTP_200_OK, detail="NetworkObjectPermission deleted")
