from fastapi import APIRouter, UploadFile, Depends, status, Request
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers.DataController import DataController
from controllers.ProjectController import ProjectController
from controllers.ProcessingController import ProcessingController
from models.ProjectModel import ProjectModel
from models.DataChunckmoel import ChunkModel
from models.AssetModel import AssetModel
from models.dbschemas import DataChunk, Asset
from models.enums.AssetTypeEnum import AssetTypeEnum
from models import ResponseSignal
from .scheams.data import processingRequest
import aiofiles
import logging
import os

logger = logging.getLogger("uvicorn.error")

data_router = APIRouter()

data_controller = DataController()
project_controller = ProjectController()


@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):

    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"signal": result_signal.value})

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

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

    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)

    asset_resource = Asset(
        asset_project_id=project.id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path),
        asset_config={
            "orig_name": file.filename,
            "content_type": file.content_type,
        },
    )

    asset_record = await asset_model.create_asset(asset=asset_resource)

    return JSONResponse(content={
        "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
        "file_id": file_id,
        "asset_id": str(asset_record.id),
    })


@data_router.post("/process/{project_id}")
async def process_data(request: Request, project_id: str,
                       process_request: processingRequest):

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)

    project_files_ids = {}

    if process_request.file_id:
        asset_record = await asset_model.get_asset_record(
            asset_project_id=project.id,
            asset_name=process_request.file_id,
        )

        if asset_record is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                content={"signal": ResponseSignal.FILE_ID_NOT_FOUND.value})

        project_files_ids = {asset_record.id: asset_record.asset_name}

    else:
        project_files = await asset_model.get_all_project_assets(
            asset_project_id=project.id,
            asset_type=AssetTypeEnum.FILE.value,
        )

        project_files_ids = {record.id: record.asset_name for record in project_files}

    if len(project_files_ids) == 0:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"signal": ResponseSignal.NO_FILES_ERROR.value})

    processing_controller = ProcessingController(project_id=project_id)
    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)

    if process_request.do_reset == 1:
        _ = await chunk_model.delete_chunks_by_project_id(project_id=project.id)

    no_records = 0
    no_files = 0

    for asset_id, file_id in project_files_ids.items():

        chunks = processing_controller.process_file(
            file_id=file_id,
            chunk_size=process_request.chunk_size,
            chunk_overlap=process_request.overlap_size,
        )

        if chunks is None or len(chunks) == 0:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                content={"signal": ResponseSignal.PROCESSING_FAILED.value})

        file_chunks_records = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=i + 1,
                chunk_project_id=project.id,
                chunk_asset_id=asset_id,
            )
            for i, chunk in enumerate(chunks)
        ]

        no_records += await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        no_files += 1

    return JSONResponse(content={
        "signal": ResponseSignal.PROCESSING_SUCCESS.value,
        "inserted_chunks": no_records,
        "processed_files": no_files,
    })
