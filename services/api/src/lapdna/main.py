"""Local read-only API. Run: python -m uvicorn lapdna.main:app --reload."""

import os
from pathlib import Path

from fastapi import FastAPI, Path as ApiPath
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from lapdna import __version__
from lapdna.models import Catalog, ComparisonArtifact, ErrorResponse, Health
from lapdna.store import ArtifactNotFound, ArtifactStore, InvalidArtifact, QualityBlocked


def create_app(artifact_dir: Path | None = None) -> FastAPI:
    application = FastAPI(title="LapDNA API", version=__version__)
    default_dir = Path(__file__).resolve().parents[4] / "data" / "artifacts"
    directory = artifact_dir or Path(os.getenv("LAPDNA_ARTIFACT_DIR", str(default_dir)))
    store = ArtifactStore(directory)
    origins = [origin.strip() for origin in os.getenv(
        "LAPDNA_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if origin.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept"],
    )

    @application.exception_handler(ArtifactNotFound)
    async def missing_artifact(_request, _error):
        return JSONResponse(status_code=404, content={"error": {
            "code": "comparison_not_found", "message": "This comparison has not been prepared."
        }})

    @application.exception_handler(InvalidArtifact)
    async def invalid_artifact(_request, _error):
        return JSONResponse(status_code=503, content={"error": {
            "code": "artifact_invalid", "message": "A comparison artifact requires repair."
        }})

    @application.exception_handler(RequestValidationError)
    async def invalid_request(_request, _error):
        return JSONResponse(status_code=422, content={"error": {
            "code": "invalid_request", "message": "The request does not match the API contract."
        }})

    @application.exception_handler(QualityBlocked)
    async def quality_blocked(_request, _error):
        return JSONResponse(status_code=503, content={"error": {
            "code": "quality_blocked", "message": "This comparison did not pass its data quality checks."
        }})

    @application.get("/api/v1/health", response_model=Health)
    def health() -> Health:
        return Health(version=__version__)

    @application.get("/api/v1/catalog", response_model=Catalog, responses={
        503: {"model": ErrorResponse},
    })
    def catalog() -> Catalog:
        return store.catalog()

    @application.get("/api/v1/comparisons/{comparison_id}", response_model=ComparisonArtifact, responses={
        404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 503: {"model": ErrorResponse},
    })
    def comparison(comparison_id: str = ApiPath(pattern=r"^[A-Za-z0-9_-]{1,100}$")) -> ComparisonArtifact:
        return store.load(comparison_id)

    return application


app = create_app()
