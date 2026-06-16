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
import permissions as perms  # KI Claude <KI-5>
from routers.base import BaseAPI

router = APIRouter(prefix="/networkObjectPermission", tags=["networkObjectPermission"], dependencies=[Depends(get_current_user)])

class NetworkObjectPermissionBase(BaseModel):
    network_object_id: int = Field(...)
    permissions: int = Field(..., ge=0, le=4)  # KI Claude <KI-5>: clamp to valid enum range

class NetworkObjectPermissionIn(NetworkObjectPermissionBase):
    # KI Claude <KI-5>
    # The granting user must say WHICH user the permission is for. Previously the
    # router silently set user_id = current_user.id, letting anyone grant
    # themselves Owner on any object -> full privilege escalation.
    target_user_id: int = Field(...)
    # KI END <KI-5>

class NetworkObjectPermissionOut(NetworkObjectPermissionBase):
    id: int = Field(..., ge=0)
    user_id: int = Field(...)

    model_config = {"from_attributes": True}

@cbv(router)
class NetworkObjectPermissionAPI(BaseAPI):
    db: Session = Depends(get_db)

    # KI Claude <KI-5>
    def assert_can_grant(self, current_user: DBUser, network_object_id: int,
                         target_user_id: int, new_level: int):
        """Enforce the role-granting rules of the permission enum.

        Roles:
          Admin (3): may grant/change permissions of users with LOWER rights than
                     the Admin, and may only assign levels 0..2 (below Admin).
          Owner (4): may grant/change anything, including Admin (3) and Owner (4).

        See/Edit/Hidden users may never grant permissions.
        """
        my_level = perms.get_permission_level(self.db, current_user, network_object_id)

        if my_level < perms.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You need Admin or Owner rights to change permissions on this object",
            )

        # The level currently held by the target user (Hidden/0 if none yet).
        target_current = self._target_level(network_object_id, target_user_id)

        if my_level == perms.ADMIN:
            # Admin may only touch users that currently have LOWER rights than him...
            if target_current >= my_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="An Admin cannot change permissions of users with equal or higher rights",
                )
            # ...and may only assign a level strictly below his own (0..2).
            if new_level >= my_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="An Admin cannot grant Admin or Owner rights",
                )
        # Owner (4) has no further restrictions.

    def _target_level(self, network_object_id: int, target_user_id: int) -> int:
        row = self.db.query(models.DBNetworkObjectPermission).filter(
            models.DBNetworkObjectPermission.user_id == target_user_id,
            models.DBNetworkObjectPermission.network_object_id == network_object_id,
        ).first()
        return row.permissions if row else perms.HIDDEN
    # KI END <KI-5>

    @router.get("/", response_model=list[NetworkObjectPermissionOut])
    def get_all_networkObjectPermissions(self, current_user: DBUser = Depends(get_current_user)):
        # KI Claude <KI-5>
        # Users always see their own permission rows. Additionally, Admins/Owners
        # of an object may see everyone's permissions on that object (needed to
        # manage roles). Global admins see all.
        if current_user.is_admin:
            return self.db.query(models.DBNetworkObjectPermission).all()

        # Objects on which the current user is Admin or Owner.
        managed_no_ids = self.db.query(models.DBNetworkObjectPermission.network_object_id).filter(
            models.DBNetworkObjectPermission.user_id == current_user.id,
            models.DBNetworkObjectPermission.permissions >= perms.ADMIN,
        )
        return self.db.query(models.DBNetworkObjectPermission).filter(
            (models.DBNetworkObjectPermission.user_id == current_user.id) |
            (models.DBNetworkObjectPermission.network_object_id.in_(managed_no_ids))
        ).all()
        # KI END <KI-5>

    @router.post("/", response_model=NetworkObjectPermissionOut, status_code=201)
    def create_networkObjectPermission(self, nOP: NetworkObjectPermissionIn, current_user: DBUser = Depends(get_current_user)):
        # KI Claude <KI-5>: enforce who may grant which level to whom
        self.assert_can_grant(current_user, nOP.network_object_id, nOP.target_user_id, nOP.permissions)

        # KI Claude detected problem why/what: a (user, object) pair must be unique,
        # otherwise a user ends up with several conflicting permission rows. If one
        # already exists, update it instead of inserting a duplicate.
        existing = self.db.query(models.DBNetworkObjectPermission).filter(
            models.DBNetworkObjectPermission.user_id == nOP.target_user_id,
            models.DBNetworkObjectPermission.network_object_id == nOP.network_object_id,
        ).first()
        if existing:
            existing.permissions = nOP.permissions
            self.db.commit()
            self.db.refresh(existing)
            return existing

        db_nOP = models.DBNetworkObjectPermission(
            user_id=nOP.target_user_id,
            network_object_id=nOP.network_object_id,
            permissions=nOP.permissions,
        )
        self.db.add(db_nOP)
        self.db.commit()
        self.db.refresh(db_nOP)
        return db_nOP
        # KI END <KI-5>

    @router.put("/{id}", status_code=201)
    def edit_networkObjectPermission(self, id: int, nOP: NetworkObjectPermissionIn, current_user: DBUser = Depends(get_current_user)):
        db_nOP = self.get_or_404(self.db, models.DBNetworkObjectPermission, id)

        # KI Claude <KI-5>
        # Check against the row's actual object/target user, not just the payload,
        # so a caller cannot retarget the row to an object he controls.
        self.assert_can_grant(current_user, db_nOP.network_object_id, db_nOP.user_id, nOP.permissions)
        # Disallow moving the row to a different object/user via PUT.
        if nOP.network_object_id != db_nOP.network_object_id or nOP.target_user_id != db_nOP.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change the object or user of an existing permission; create a new one instead",
            )
        db_nOP.permissions = nOP.permissions
        # KI END <KI-5>

        self.db.refresh(db_nOP)
        self.db.commit()

        raise HTTPException(status_code=status.HTTP_200_OK, detail="NetworkObjectPermission updated")

    @router.delete("/{id}")
    def delete_networkObjectPermission(self, id: int, current_user: DBUser = Depends(get_current_user)):
        db_nOP = self.get_or_404(self.db, models.DBNetworkObjectPermission, id)

        # KI Claude <KI-5>: removing a permission == setting it to Hidden(0), same rules apply
        self.assert_can_grant(current_user, db_nOP.network_object_id, db_nOP.user_id, perms.HIDDEN)
        # KI END <KI-5>

        self.db.delete(db_nOP)
        self.db.commit()

        raise HTTPException(status_code=status.HTTP_200_OK, detail="NetworkObjectPermission deleted")
