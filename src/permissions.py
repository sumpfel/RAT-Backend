# KI Claude <KI-1>
# Central permission helpers for NetworkObject access control.
# Mirrors the C# enum NetworkObjectPermission:
#   Hidden = 0  -> don't see device or its connections at all
#   See    = 1  -> can see device + interfaces (logins/snmp are per-user)
#   Edit   = 2  -> change interfaces and settings (name etc), NOT delete
#   Admin  = 3  -> Edit + change permissions of users with LOWER rights on this object
#   Owner  = 4  -> change admins, grant/remove Owner, delete the object
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

import models
from models import DBUser

# Permission level constants (keep in sync with the C# enum / frontend)
HIDDEN = 0
SEE = 1
EDIT = 2
ADMIN = 3
OWNER = 4


def get_permission_level(db: Session, user: DBUser, network_object_id: int) -> int:
    """Return the effective permission level a user has on a NetworkObject.

    If no NetworkObjectPermission row points from the user to the object, the
    user is treated as HIDDEN (0) - same as an explicit permission of 0.
    Global admins (is_admin) always get OWNER.
    """
    if user.is_admin:
        return OWNER

    db_nOP = db.query(models.DBNetworkObjectPermission).filter(
        models.DBNetworkObjectPermission.user_id == user.id,
        models.DBNetworkObjectPermission.network_object_id == network_object_id,
    ).first()

    if db_nOP is None:
        return HIDDEN
    return db_nOP.permissions


def require_permission(db: Session, user: DBUser, network_object_id: int, min_level: int) -> int:
    """Ensure the user has at least `min_level` on the object, else raise 403.

    Returns the actual permission level so callers can use it for finer checks.
    Note: HIDDEN objects are reported as 404 (not 403) so a user cannot even
    learn that an object they may not see exists.
    """
    level = get_permission_level(db, user, network_object_id)

    if level <= HIDDEN:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NetworkObject not found",
        )
    if level < min_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have sufficient permissions on this NetworkObject",
        )
    return level
# KI END <KI-1>
