from sqlalchemy import Column, Integer, String, Float, VARCHAR, ForeignKey, Boolean
from database import Base

class DBUser(Base):
    __tablename__ = "User"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_settings_id = Column(Integer, ForeignKey("UserSettings.id"), index=True)
    username = Column(VARCHAR(50), unique=True, nullable=False)
    password = Column(VARCHAR(50), nullable=False)
    privileges = Column(Integer, nullable=False, default=0)

class DBUserSettings(Base):
    __tablename__ = "UserSettings"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    zoom = Column(Integer, default=100)
    show_ports = Column(Boolean, default=False)
    show_interfaces = Column(Boolean, default=False)

class DBNetworkObjectPermissions(Base):
    __tablename__ = "NetworkObjectPermissions"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("User.id"), index=True)
    network_object_id = Column(Integer, ForeignKey("NetworkObject.id"), index=True)
    visible = Column(Boolean, default=False)
    read_status = Column(Boolean, default=False)
    read_advanced = Column(Boolean, default=False)

class DBNetworkObject(Base):
    __tablename__ = "NetworkObject"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    json_data = Column(String)

class DBNetworkObjectConnectionLink(Base):
    __tablename__ = "NetworkObjectConnectionLink"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    network_object_id = Column(Integer, ForeignKey("NetworkObject.id"), index=True)
    network_object_connection_id = Column(Integer, ForeignKey("NetworkObjectConnection.id"), index=True)

class DBNetworkObjectConnection(Base):
    __tablename__ = "NetworkObjectConnection"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    json_data = Column(String)

class DBNetworkObjectLogin(Base):
    __tablename__ = "NetworkObjectLogin"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    network_object_id = Column(Integer, ForeignKey("NetworkObject.id"), index=True)
    user_id = Column(Integer, ForeignKey("User.id"), index=True)
    port = Column(Integer)
    user = Column(VARCHAR(50))
    password = Column(VARCHAR(50))
    key = Column(String)

class DBNetworkObjectSnmpCommunity(Base):
    __tablename__ = "NetworkObjectSnmpCommunity"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    network_object_id = Column(Integer, ForeignKey("NetworkObject.id"), index=True)
    user_id = Column(Integer, ForeignKey("User.id"), index=True)
    read_community = Column(VARCHAR(50))
    write_community = Column(VARCHAR(50))