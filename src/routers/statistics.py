# KI Claude <KI-16>
# Aggregation & statistics endpoints (required: at least one GROUP BY + COUNT/SUM/AVG).
#
# These read-only endpoints answer the "nice to have" goals from the project planning
# (Statistiken: wie viele Geräte/Kabel, Bottlenecks ...). All queries use the SQLAlchemy
# ORM with bound parameters, so they are safe against SQL injection.
#
# Visibility: a normal user only sees statistics over the NetworkObjects they may See(1)+;
# a global admin sees everything. This mirrors the per-object permission checks of the
# other routers so statistics can't leak the existence of hidden objects.
from fastapi import APIRouter
from fastapi.params import Depends
from fastapi_restful.cbv import cbv
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
import models
from models import DBUser
import permissions

router = APIRouter(prefix="/statistics", tags=["statistics"], dependencies=[Depends(get_current_user)])


@cbv(router)
class StatisticsAPI:
    db: Session = Depends(get_db)

    def _visible_object_ids(self, current_user: DBUser):
        """IDs of the NetworkObjects the user may see (None == all, for a global admin)."""
        if current_user.is_admin:
            return None
        rows = self.db.query(models.DBNetworkObjectPermission.network_object_id).filter(
            models.DBNetworkObjectPermission.user_id == current_user.id,
            models.DBNetworkObjectPermission.permissions >= permissions.SEE,
        ).all()
        return [r[0] for r in rows]

    @router.get("/summary")
    def summary(self, current_user: DBUser = Depends(get_current_user)):
        """High-level counts: how many objects / interfaces / connections are visible,
        plus AVG/SUM/MAX over connection speeds (COUNT + AVG + SUM + MAX aggregation)."""
        visible_ids = self._visible_object_ids(current_user)

        obj_q = self.db.query(models.DBNetworkObject)
        iface_q = self.db.query(models.DBNetworkObjectInterface)
        if visible_ids is not None:
            obj_q = obj_q.filter(models.DBNetworkObject.id.in_(visible_ids))
            iface_q = iface_q.filter(models.DBNetworkObjectInterface.network_object_id.in_(visible_ids))

        # connections visible == connections whose interfaces belong to a visible object
        conn_q = self.db.query(models.DBNetworkObjectConnection)
        if visible_ids is not None:
            visible_conn_ids = self.db.query(models.DBNetworkObjectInterface.network_object_connection_id).filter(
                models.DBNetworkObjectInterface.network_object_id.in_(visible_ids),
                models.DBNetworkObjectInterface.network_object_connection_id.isnot(None),
            )
            conn_q = conn_q.filter(models.DBNetworkObjectConnection.id.in_(visible_conn_ids))

        speed_stats = conn_q.with_entities(
            func.avg(models.DBNetworkObjectConnection.speed),
            func.sum(models.DBNetworkObjectConnection.speed),
            func.max(models.DBNetworkObjectConnection.speed),
            func.min(models.DBNetworkObjectConnection.speed),
        ).first()

        return {
            "network_objects": obj_q.count(),
            "interfaces": iface_q.count(),
            "connections": conn_q.count(),
            "connection_speed": {
                "avg": float(speed_stats[0]) if speed_stats[0] is not None else None,
                "sum": int(speed_stats[1]) if speed_stats[1] is not None else 0,
                "max": int(speed_stats[2]) if speed_stats[2] is not None else None,
                "min": int(speed_stats[3]) if speed_stats[3] is not None else None,
            },
        }

    @router.get("/objects-by-type")
    def objects_by_type(self, current_user: DBUser = Depends(get_current_user)):
        """GROUP BY NetworkObject.type with COUNT -> how many devices of each type.

        Example: [{"type": "PC", "count": 4}, {"type": "Switch", "count": 2}]
        """
        visible_ids = self._visible_object_ids(current_user)

        query = self.db.query(
            models.DBNetworkObject.type,
            func.count(models.DBNetworkObject.id).label("count"),
        )
        if visible_ids is not None:
            query = query.filter(models.DBNetworkObject.id.in_(visible_ids))

        rows = query.group_by(models.DBNetworkObject.type).all()
        return [{"type": t, "count": c} for t, c in rows]

    @router.get("/connections-by-type")
    def connections_by_type(self, current_user: DBUser = Depends(get_current_user)):
        """GROUP BY NetworkObjectConnection.type with COUNT + AVG/SUM over the speed
        -> for each cable type: how many there are and the average / total speed."""
        visible_ids = self._visible_object_ids(current_user)

        query = self.db.query(
            models.DBNetworkObjectConnection.type,
            func.count(models.DBNetworkObjectConnection.id).label("count"),
            func.avg(models.DBNetworkObjectConnection.speed).label("avg_speed"),
            func.sum(models.DBNetworkObjectConnection.speed).label("total_speed"),
        )
        if visible_ids is not None:
            visible_conn_ids = self.db.query(models.DBNetworkObjectInterface.network_object_connection_id).filter(
                models.DBNetworkObjectInterface.network_object_id.in_(visible_ids),
                models.DBNetworkObjectInterface.network_object_connection_id.isnot(None),
            )
            query = query.filter(models.DBNetworkObjectConnection.id.in_(visible_conn_ids))

        rows = query.group_by(models.DBNetworkObjectConnection.type).all()
        return [
            {
                "type": t,
                "count": c,
                "avg_speed": float(avg) if avg is not None else None,
                "total_speed": int(total) if total is not None else 0,
            }
            for t, c, avg, total in rows
        ]

    @router.get("/interfaces-per-object")
    def interfaces_per_object(self, current_user: DBUser = Depends(get_current_user)):
        """GROUP BY NetworkObject with COUNT of its interfaces -> how many interfaces each
        device has (helps spot the busiest devices). Includes objects with zero interfaces."""
        visible_ids = self._visible_object_ids(current_user)

        query = self.db.query(
            models.DBNetworkObject.id,
            models.DBNetworkObject.name,
            func.count(models.DBNetworkObjectInterface.id).label("interface_count"),
        ).outerjoin(
            models.DBNetworkObjectInterface,
            models.DBNetworkObjectInterface.network_object_id == models.DBNetworkObject.id,
        )
        if visible_ids is not None:
            query = query.filter(models.DBNetworkObject.id.in_(visible_ids))

        rows = query.group_by(models.DBNetworkObject.id, models.DBNetworkObject.name).all()
        return [
            {"network_object_id": oid, "name": name, "interface_count": cnt}
            for oid, name, cnt in rows
        ]
# KI END <KI-16>
