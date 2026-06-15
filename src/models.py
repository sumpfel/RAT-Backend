from typing import Text

from sqlalchemy import Column, Integer, String, Float, VARCHAR, ForeignKey, Boolean
from database import Base

class DBUser(Base):
    __tablename__ = "User"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(VARCHAR(50), unique=True, nullable=False)
    password = Column(VARCHAR(70), nullable=False)
    privileges = Column(Integer, nullable=False, default=0)
    canCreate = Column(Boolean, default=False)

class DBUserSettings(Base):
    __tablename__ = "UserSettings"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("User.id"), index=True)
    zoom = Column(Integer, default=1)
    showPorts = Column(Boolean, default=False)
    showInterfaces = Column(Boolean, default=False)


class DBNetworkObjectPermission(Base):
    __tablename__ = "NetworkObjectPermission"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("User.id"), index=True)
    network_object_id = Column(Integer, ForeignKey("NetworkObject.id"), index=True)
    permissions = Column(Integer, nullable=False, default=0)

    # removed
    # visible = Column(Boolean, default=False)
    # read_status = Column(Boolean, default=False)
    # read_advanced = Column(Boolean, default=False)

class DBSNMPSettings(Base):
    __tablename__ = "SNMPSettings"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    network_object_permission_id = Column(Integer, ForeignKey("NetworkObjectPermission.id"), index=True)
    read_community = Column(VARCHAR(50), index=True)
    write_community = Column(VARCHAR(50), index=True)

class DBLogin(Base):
    __tablename__ = "Login"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    network_object_permission_id = Column(Integer, ForeignKey("NetworkObjectPermission.id"), index=True)
    port = Column(Integer)
    type = Column(VARCHAR(10))
    username = Column(VARCHAR(50))
    password = Column(VARCHAR(50))

class DBNetworkObject(Base):
    __tablename__ = "NetworkObject"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(VARCHAR(50), unique=True, nullable=False)
    type = Column(VARCHAR(20), index=True)
    x = Column(Integer)
    y = Column(Integer)
    os = Column(VARCHAR(100), index=True)
    cpu = Column(VARCHAR(100), index=True)
    gpu = Column(VARCHAR(100), index=True)
    ram = Column(VARCHAR(100), index=True)
    specs = Column(String, index=True)

class DBNetworkObjectInterface(Base):
    __tablename__ = "NetworkObjectInterface"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    network_object_id = Column(Integer, ForeignKey("NetworkObject.id"), index=True)
    network_object_connection_id = Column(Integer, ForeignKey("NetworkObjectConnection.id"), index=True)
    name = Column(VARCHAR(50), index=True)
    max_speed = Column(Integer)
    is_up = Column(Boolean, default=False)
    ipv4 = Column(VARCHAR(15), index=True)
    ipv6 = Column(VARCHAR(45), index=True)
    ipv4_subnet_mask = Column(VARCHAR(15), index=True)
    ipv6_prefix_length = Column(Integer)
    ipv4_gateway = Column(VARCHAR(15), index=True)

class DBNetworkObjectConnection(Base):
    __tablename__ = "NetworkObjectConnection"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(VARCHAR(50), index=True)
    speed = Column(Integer)
    type = Column(VARCHAR(20), index=True)
    note = Column(String)