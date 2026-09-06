from fastapi import APIRouter, UploadFile, Depends,status
from helpers.config import get_settings, Settings
from fastapi.responses import JSONResponse
from controllers.DataController import DataController
from controllers.ProjectController import ProjectController
from controllers.ProcessingController import ProcessingController
import aiofiles
from .scheams.data import processingRequest
from models import ResponseSignal
import logging
import os

logger = logging.getLogger("uvicorn.error")
data_router = APIRouter()
data_controller = DataController()
project_controller=ProjectController()
@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):

    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"signal": result_signal.value})

    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename, project_id=project_id)

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f"Error while uploading file: {e}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"signal": ResponseSignal.FILE_UPLOAD_FAILED.value})

    return JSONResponse(content={"signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
                                 "file_id": file_id})

@data_router.post("/process/{project_id}")
def process_data(project_id:str,process_request: processingRequest):
    processing_controller=ProcessingController(project_id=project_id)
    chunks=processing_controller.process_file(file_id=process_request.file_id,chunk_size=process_request.chunk_size,chunk_overlap=process_request.overlap_size)
    if chunks is None:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"signal": ResponseSignal.PROCESSING_FAILED.value})
    return  chunks