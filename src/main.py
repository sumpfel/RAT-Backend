# KI Claude <KI-20>
# Make the app importable both as `main:app` (cwd == src/, used by run.sh) and as
# `src.main:app` (cwd == project root, the required `uvicorn src.main:app` form).
# The modules import each other flat (e.g. `from database import ...`), which only
# resolves if src/ is on sys.path. When loaded as `src.main` that is not the case,
# so we add this file's own directory (src/) to sys.path before the flat imports.
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# KI END <KI-20>

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
import uvicorn
from starlette import status
from starlette.responses import JSONResponse
import logging
from database import engine, SessionLocal
import models
from auth import hash_password  # KI Claude <KI-8>
from routers import user, userSettings, networkObject, networkObjectConnection, networkObjectInterface, networkObjectPermission, login, snmpSettings, statistics  # KI Claude <KI-16>

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

# KI Claude <KI-15>
# Logging is mandatory: every incoming request and every error must be logged with
# Python's built-in logging module, written to BOTH the console and a file (api.log).
#   - INFO  for normal requests (method, path, status code)
#   - ERROR for unexpected errors (with the exception)
# (Previously this logged to "rat.tail" and never logged errors.)
# KI Claude <KI-20>: anchor api.log next to this module (src/api.log) so it lands in the
# same place regardless of the working directory the server was started from.
_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(_LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # INFO log for every incoming request: method, path and resulting status code.
    response = await call_next(request)
    logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
    return response

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # ERROR log for any unexpected/unhandled error, then a clean 500 to the client
    # (so we never leak a stack trace / DB internals in the HTTP response).
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": "error", "message": "Internal server error"},
    )
# KI END <KI-15>

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = error.get("loc")[-1]
        error_msg = error.get("msg")

        errors.append({"field": field, "message": error_msg})

    # KI Claude <KI-15>: also log validation failures as warnings
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, errors)
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "validation_error", "errors": errors})

# app.include(xxx.router)
app.include_router(networkObject.router)
app.include_router(networkObjectConnection.router)
app.include_router(networkObjectInterface.router)
app.include_router(networkObjectPermission.router)
app.include_router(login.router)
app.include_router(snmpSettings.router)
app.include_router(statistics.router)  # KI Claude <KI-16>

app.include_router(user.router)
app.include_router(userSettings.router)  # KI Claude detected problem why/what: userSettings router was never registered

@app.get("/")
def root():
    return {"message": "Willkommen bei der RAT-Backend API! Besuche /docs für die SwaggerUI."}

if __name__ == '__main__':
    # TODO: Make IP and Port Configurable (config.txt)
    uvicorn.run(app, host="127.0.0.1", port=8000)