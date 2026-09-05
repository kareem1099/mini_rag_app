from fastapi import  APIRouter,Depends
from helpers.config import get_settings ,Settings
base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"]
)
settings = Depends(get_settings)


@base_router.get("/healthy")
async def healthy(settings: Settings = Depends(get_settings)):
    
    return {"Appname": settings.APP_NAME, "version": settings.VERSION, "status": "healthy"}
