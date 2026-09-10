from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from models.ProjectModel import ProjectModel
from models.DataChunckmoel import ChunkModel
from models import ResponseSignal
from controllers.NLPController import NLPController
from .scheams.nlp import PushRequest, SearchRequest
import logging

logger = logging.getLogger("uvicorn.error")

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)


def build_nlp_controller(request: Request):
    return NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
    )


@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: str, push_request: PushRequest):

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value})

    nlp_controller = build_nlp_controller(request)

    _ = nlp_controller.create_vector_db_collection(
        project=project,
        do_reset=bool(push_request.do_reset),
    )

    has_records = True
    page_no = 1
    idx = 0
    inserted_items_count = 0

    while has_records:
        page_chunks = await chunk_model.get_project_chunks(project_id=project.id,
                                                           page_no=page_no)

        if not page_chunks or len(page_chunks) == 0:
            has_records = False
            break

        page_no += 1

        chunks_ids = list(range(idx, idx + len(page_chunks)))
        idx += len(page_chunks)

        is_inserted = nlp_controller.index_into_vector_db(
            project=project,
            chunks=page_chunks,
            chunks_ids=chunks_ids,
        )

        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"signal": ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value})

        inserted_items_count += len(page_chunks)

    return JSONResponse(content={
        "signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
        "inserted_items_count": inserted_items_count,
    })


@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: str):

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value})

    nlp_controller = build_nlp_controller(request)
    collection_info = nlp_controller.get_vector_db_collection_info(project=project)

    return JSONResponse(content={
        "signal": ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
        "collection_info": collection_info,
    })


@nlp_router.post("/index/search/{project_id}")
async def search_index(request: Request, project_id: str, search_request: SearchRequest):

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value})

    nlp_controller = build_nlp_controller(request)

    results = nlp_controller.search_vector_db_collection(
        project=project,
        text=search_request.text,
        limit=search_request.limit,
    )

    if not results:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.VECTORDB_SEARCH_ERROR.value})

    return JSONResponse(content={
        "signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
        "results": results,
    })
