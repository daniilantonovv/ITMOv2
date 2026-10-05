import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.models import CategoryCount, Collection, CollectionIn, CollectionSummary
from app.storage import CollectionStore, DuplicateCartUrlError, StorageUnavailableError

STATIC_DIR = Path(__file__).parent / "static"
DEFAULT_DB = "data/collections.db"


def create_app(db_path: Path | str | None = None) -> FastAPI:
    store = CollectionStore(db_path or os.environ.get("COLLECTIONS_DB", DEFAULT_DB))
    api = APIRouter(prefix="/api")

    def found(collection: Collection | None) -> Collection:
        if collection is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="collection not found")
        return collection

    @api.post("/collections", status_code=status.HTTP_201_CREATED)
    def create_collection(data: CollectionIn) -> Collection:
        return store.create(data)

    @api.get("/collections")
    def list_collections(
        limit: Annotated[int, Query(ge=1, le=100)] = 10,
        category: str | None = None,
    ) -> list[CollectionSummary]:
        return [c.summary() for c in store.list(limit=limit, category=category)]

    @api.get("/collections/{collection_id}")
    def get_collection(collection_id: int) -> Collection:
        return found(store.get(collection_id))

    @api.put("/collections/{collection_id}")
    def update_collection(collection_id: int, data: CollectionIn) -> Collection:
        return found(store.update(collection_id, data))

    @api.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_collection(collection_id: int) -> Response:
        if not store.delete(collection_id):
            found(None)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @api.get("/categories")
    def list_categories() -> list[CategoryCount]:
        return store.categories()

    app = FastAPI(title="VkusVill Collections")

    @app.exception_handler(DuplicateCartUrlError)
    def handle_duplicate_cart_url(request: Request, exc: DuplicateCartUrlError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "collection with this cart_url already exists"},
        )

    @app.exception_handler(StorageUnavailableError)
    def handle_storage_unavailable(request: Request, exc: StorageUnavailableError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "storage unavailable"},
        )

    app.include_router(api)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app

