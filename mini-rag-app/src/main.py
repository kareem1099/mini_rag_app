from fastapi import FastAPI
from routes.base import base_router
from routes.data import data_router
from helpers.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient


app = FastAPI()
app.include_router(base_router)
app.include_router(data_router)
@app.on_event("startup")
async def startup_db_client():
    settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongo_conn.close()

    
