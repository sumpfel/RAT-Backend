from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
import uvicorn
from starlette import status
from starlette.responses import JSONResponse

from database import engine
import models
from routers import user

models.Base.metadata.create_all(bind=engine)

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

@app.get("/")
def root():
    return {"message": "Willkommen bei der RAT-Backend API! Besuche /docs für die SwaggerUI."}

if __name__ == '__main__':
    # TODO: Make IP and Port Configurable (config.txt)
    uvicorn.run(app, host="127.0.0.0", port=8000)