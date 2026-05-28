from sqlalchemy import Column, Integer, String, Float, VARCHAR, ForeignKey, Boolean
from database import Base

class DBUser(Base):
    __tablename__ = "User"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_settings_id = Column(Integer, ForeignKey("usersettings.id"))
    username = Column(VARCHAR(50), unique=True, notnull=True)
    password = Column(VARCHAR(50), notnull=True)
    privileges = Column(Integer, notnull=True)

class DBUserSettings(Base):
    __tablename__ = "UserSettings"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    json_data = Column(VARCHAR(1000))

class DBNetworkObjectPermissions(Base):
    __tablename__ = "NetworkObjectPermissions"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True)
    network_object_id = Column(Integer, ForeignKey("networkobject.id"), index=True)
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
    network_object_id = Column(Integer, ForeignKey("networkobject.id"), index=True)
    network_object_connection_id = Column(Integer, ForeignKey("networkobjectconnection.id"), index=True)

class DBNetworkObjectConnection(Base):
    __tablename__ = "NetworkObjectConnection"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    json_data = Column(String)

class DBNetworkObjectLogin(Base):
    __tablename__ = "NetworkObjectLogin"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    network_object_id = Column(Integer, ForeignKey("networkobject.id"), index=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True)
    port = Column(Integer)
    user = Column(VARCHAR(50))
    password = Column(VARCHAR(50))
    key = Column(String)

class DBNetworkObjectSnmpCommunity(Base):
    __tablename__ = "NetworkObjectSnmpCommunity"
    network_object_id = Column(Integer, ForeignKey("networkobject.id"), index=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True)
    read_community = Column(VARCHAR(50))
    write_community = Column(VARCHAR(50))