from fastapi import FastAPI
from database import engine
import models

models.Base.metadata.create_all(bind=engine)

# Haupt-API-Instanz erzeugen
app = FastAPI(
    title="RAT-Backend",
    description="Backend for RAT(Remote Access Topologie)",
    version="1.0.0"
)

# app.include(xxx.router)

@app.get("/")
def root():
    return {"message": "Willkommen bei der RAT-Backend API! Besuche /docs für die SwaggerUI."}