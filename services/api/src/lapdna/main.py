"""Local read-only API. Run: python -m uvicorn lapdna.main:app --reload."""

import os
from pathlib import Path

from fastapi import FastAPI, Path as ApiPath
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from lapdna import __version__
from lapdna.calendar import CalendarSeason, CalendarService, CalendarUnavailable, Seasons
from lapdna.inventory import (
    CompareRequest, CompareResponse, SelectionError, SessionInventory, SessionLapIndex, SessionStore,
)
from lapdna.models import Artifact, Catalog, ErrorResponse, Health
from lapdna.store import ArtifactNotFound, ArtifactStore, InvalidArtifact, QualityBlocked


def create_app(artifact_dir: Path | None = None, session_dir: Path | None = None,
               calendar_service: CalendarService | None = None) -> FastAPI:
    application = FastAPI(title="LapDNA API", version=__version__)
    calendars = calendar_service or CalendarService()
    default_dir = Path(__file__).resolve().parents[4] / "data" / "artifacts"
    directory = artifact_dir or Path(os.getenv("LAPDNA_ARTIFACT_DIR", str(default_dir)))
    store = ArtifactStore(directory)
    sessions = SessionStore(session_dir or Path(os.getenv("LAPDNA_SESSION_DIR", str(directory.parent / "sessions"))))
    origins = [origin.strip() for origin in os.getenv(
        "LAPDNA_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if origin.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Accept", "Content-Type"],
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

    @application.exception_handler(SelectionError)
    async def invalid_selection(_request, error: SelectionError):
        return JSONResponse(status_code=error.status, content={"error": {
            "code": error.code, "message": error.message,
        }})

    @application.get("/api/v1/health", response_model=Health)
    def health() -> Health:
        return Health(version=__version__)

    @application.exception_handler(CalendarUnavailable)
    async def unavailable_calendar(_request, error: CalendarUnavailable):
        return JSONResponse(status_code=error.status, content={"error": {
            "code": error.code, "message": error.message,
        }})

    @application.get("/api/v1/seasons", response_model=Seasons)
    def seasons() -> Seasons:
        return calendars.seasons()

    @application.get("/api/v1/calendar/{year}", response_model=CalendarSeason, responses={
        422: {"model": ErrorResponse}, 503: {"model": ErrorResponse},
    })
    def calendar(year: int = ApiPath(ge=1950, le=2100)) -> CalendarSeason:
        return calendars.get(year)

    @application.get("/api/v1/catalog", response_model=Catalog, responses={
        503: {"model": ErrorResponse},
    })
    def catalog() -> Catalog:
        return store.catalog()

    @application.get("/api/v1/comparisons/{comparison_id}", response_model=Artifact, responses={
        404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 503: {"model": ErrorResponse},
    })
    def comparison(comparison_id: str = ApiPath(pattern=r"^[A-Za-z0-9_-]{1,100}$")) -> Artifact:
        return store.load(comparison_id)

    @application.get("/api/v1/sessions", response_model=SessionInventory, responses={503: {"model": ErrorResponse}})
    def session_inventory() -> SessionInventory:
        return sessions.inventory()

    @application.get("/api/v1/sessions/{session_id}/laps", response_model=SessionLapIndex, responses={
        404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 503: {"model": ErrorResponse},
    })
    def session_laps(session_id: str = ApiPath(pattern=r"^[A-Za-z0-9_-]{1,100}$")) -> SessionLapIndex:
        try:
            return sessions.load(session_id)
        except ArtifactNotFound as exc:
            raise SelectionError(404, "session_not_found", "This session has not been imported.") from exc

    @application.post("/api/v1/compare", response_model=CompareResponse, responses={
        404: {"model": ErrorResponse}, 409: {"model": ErrorResponse},
        422: {"model": ErrorResponse}, 503: {"model": ErrorResponse},
    })
    def compare(request: CompareRequest) -> CompareResponse:
        return sessions.compare(request, store)

    return application


app = create_app()
