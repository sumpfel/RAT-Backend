#!/usr/bin/env python3
# KI Claude <KI-20>
# Standalone database-initialization script (required at the project root by the
# submission structure).
#
# It creates all tables defined in src/models.py, a default admin account (admin/admin)
# and a set of DUMMY TEST DATA (extra users, network objects, interfaces, a connection,
# per-object permissions, a login and SNMP settings) so the database can be inspected /
# tested right away.
#
# By default it writes directly into the project's database file src/RATBASE.db (the same
# file the API uses). Set DATABASE_URL to target a different / Cloud database instead.
#
# Usage (from the project root):
#     python init_db.py
#     DATABASE_URL=postgresql+psycopg2://user:pw@host:5432/db  python init_db.py
import os
import sys

# src/ on the path so the flat-importing modules resolve, and default the DB file to
# src/RATBASE.db (so init_db.py writes into the same DB the server reads).
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, SRC)
os.environ.setdefault("DATABASE_URL", "sqlite:///" + os.path.join(SRC, "RATBASE.db"))

from database import engine, SessionLocal, SQLALCHEMY_DATABASE_URL  # noqa: E402
import models  # noqa: E402
from auth import hash_password  # noqa: E402
import permissions  # noqa: E402


def init_db() -> None:
    print(f"Using database: {SQLALCHEMY_DATABASE_URL}")

    # 1) create every table from the models
    models.Base.metadata.create_all(bind=engine)
    print("Tables created (or already present).")

    db = SessionLocal()
    try:
        if db.query(models.DBUser).first() is not None:
            print("Database already contains users - skipping seed "
                  "(delete the DB file to re-seed).")
            return

        # 2) default admin + a normal user
        admin = models.DBUser(username="admin", password=hash_password("admin"),
                              is_admin=True, canCreate=True)
        bob = models.DBUser(username="bob", password=hash_password("bobbob12"),
                            is_admin=False, canCreate=True)
        db.add_all([admin, bob])
        db.commit()
        db.refresh(admin)
        db.refresh(bob)

        db.add(models.DBUserSettings(user_id=admin.id, zoom=100))
        db.add(models.DBUserSettings(user_id=bob.id, zoom=120, showInterfaces=True))
        db.commit()

        # 3) dummy network objects (devices)
        pc = models.DBNetworkObject(name="PC-1", type="PC", x=120, y=80,
                                    os="Arch Linux", cpu="Ryzen 5", gpu="RTX 3060",
                                    ram="16GB", specs="workstation")
        sw = models.DBNetworkObject(name="Switch-1", type="Switch", x=320, y=80,
                                    os="Cisco IOS", cpu="-", gpu="-", ram="-",
                                    specs="24-port managed switch")
        db.add_all([pc, sw])
        db.commit()
        db.refresh(pc)
        db.refresh(sw)

        # 4) a connection (cable) and one interface on each device pointing at it
        conn = models.DBNetworkObjectConnection(name="PC-1 <-> Switch-1", speed=1000,
                                                type="Ethernet", note="copper, 1 Gbit/s")
        db.add(conn)
        db.commit()
        db.refresh(conn)

        if_pc = models.DBNetworkObjectInterface(
            network_object_id=pc.id, network_object_connection_id=conn.id,
            name="eth0", max_speed=1000, is_up=True,
            ipv4="192.168.1.10", ipv6="fe80::10", ipv4_subnet_mask="255.255.255.0",
            ipv6_prefix_length=64, ipv4_gateway="192.168.1.1")
        if_sw = models.DBNetworkObjectInterface(
            network_object_id=sw.id, network_object_connection_id=conn.id,
            name="Gi0/1", max_speed=1000, is_up=True,
            ipv4="192.168.1.1", ipv6="fe80::1", ipv4_subnet_mask="255.255.255.0",
            ipv6_prefix_length=64, ipv4_gateway="192.168.1.1")
        db.add_all([if_pc, if_sw])
        db.commit()

        # 5) permissions: admin owns both; bob may See PC-1 and Edit Switch-1
        admin_perm_pc = models.DBNetworkObjectPermission(
            user_id=admin.id, network_object_id=pc.id, permissions=permissions.OWNER)
        admin_perm_sw = models.DBNetworkObjectPermission(
            user_id=admin.id, network_object_id=sw.id, permissions=permissions.OWNER)
        bob_perm_pc = models.DBNetworkObjectPermission(
            user_id=bob.id, network_object_id=pc.id, permissions=permissions.SEE)
        bob_perm_sw = models.DBNetworkObjectPermission(
            user_id=bob.id, network_object_id=sw.id, permissions=permissions.EDIT)
        db.add_all([admin_perm_pc, admin_perm_sw, bob_perm_pc, bob_perm_sw])
        db.commit()
        db.refresh(bob_perm_pc)

        # 6) a device login + SNMP settings hanging off bob's See-permission on PC-1
        db.add(models.DBLogin(network_object_permission_id=bob_perm_pc.id, port=22,
                              type="ssh", username="bob", password="secret123"))
        db.add(models.DBSNMPSettings(network_object_permission_id=bob_perm_pc.id,
                                     read_community="public", write_community="private"))
        db.commit()

        print("Seeded dummy data:")
        print(f"  users:        {db.query(models.DBUser).count()} (admin/admin, bob/bobbob12)")
        print(f"  objects:      {db.query(models.DBNetworkObject).count()}")
        print(f"  interfaces:   {db.query(models.DBNetworkObjectInterface).count()}")
        print(f"  connections:  {db.query(models.DBNetworkObjectConnection).count()}")
        print(f"  permissions:  {db.query(models.DBNetworkObjectPermission).count()}")
        print(f"  logins:       {db.query(models.DBLogin).count()}")
        print(f"  snmp settings:{db.query(models.DBSNMPSettings).count()}")
    finally:
        db.close()

    print("Database initialization done.")


if __name__ == "__main__":
    init_db()
# KI END <KI-20>
