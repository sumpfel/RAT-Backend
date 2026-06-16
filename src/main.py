from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
import uvicorn
from starlette import status
from starlette.responses import JSONResponse

from database import engine, SessionLocal
import models
from auth import hash_password  # KI Claude <KI-8>
from routers import user, userSettings, networkObject, networkObjectConnection, networkObjectInterface, networkObjectPermission, login, snmpSettings

models.Base.metadata.create_all(bind=engine)


# KI Claude <KI-8>
# On first start (fresh DB / no users), create a default admin account
# (username "admin", password "admin") plus its UserSettings so the app is usable.
# SECURITY: change this password immediately after the first login.
def create_default_admin():
    db = SessionLocal()
    try:
        if db.query(models.DBUser).first() is None:
            admin = models.DBUser(
                username="admin",
                password=hash_password("admin"),
                is_admin=True,
                canCreate=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            db.add(models.DBUserSettings(user_id=admin.id))
            db.commit()
            print("Created default admin user (username='admin', password='admin'). Change this password!")
    finally:
        db.close()


create_default_admin()
# KI END <KI-8>

# Haupt-API-Instanz erzeugen
app = FastAPI(
    title="RAT-Backend",
    description="Backend for RAT(Remote Access Topologie)",
    version="1.0.0"
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = error.get("loc")[-1]
        error_msg = error.get("msg")

        errors.append({"field": field, "message": error_msg})

    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "validation_error", "errors": errors})

# app.include(xxx.router)
app.include_router(networkObject.router)
app.include_router(networkObjectConnection.router)
app.include_router(networkObjectInterface.router)
app.include_router(networkObjectPermission.router)
app.include_router(login.router)
app.include_router(snmpSettings.router)

app.include_router(user.router)
app.include_router(userSettings.router)  # KI Claude detected problem why/what: userSettings router was never registered

@app.get("/")
def root():
    return {"message": "Willkommen bei der RAT-Backend API! Besuche /docs für die SwaggerUI."}

if __name__ == '__main__':
    # TODO: Make IP and Port Configurable (config.txt)
    uvicorn.run(app, host="127.0.0.1", port=8000)