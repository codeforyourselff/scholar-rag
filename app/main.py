# Main entry point for the Scholar RAG Web Application
import os
import logging
from uvicorn import run
from fastapi import Depends, FastAPI, Request
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.container import Container, build_container
logger = logging.getLogger(__name__)

def get_container(request: Request) -> Container:
    """Dependency: pull the wired container off app.state (built during lifespan)."""
    app : FastAPI = request.app
    return app.state.container

# manage the lifecycle of external resources (e.g., database connections, background tasks)
@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncIterator[None]:
    # Startup logic here
    settings : Settings = app.state.settings
    container = build_container(settings)
    await container.startup()
    app.state.container = container
    try:
        yield
    finally:
        await container.shutdown()

# Function to create the FastAPI application

def create_application(settings: Settings = get_settings()) -> FastAPI:
    logging.basicConfig(level=settings.log_level.upper())

    app = FastAPI(
        title="Scholar RAG Web App",
        version=settings.version,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        description="A web application for the Scholar RAG system.",
        lifespan=lifespan
    )

    # Stash settigns so lifespan can read them at startup
    app.state.settings = settings

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict[str, str]:
        # Liveness: the process is up. Must NOT depend on backends.
        return {"status": "ok"}
    
    @app.get("/readyz", tags=["health"])
    async def readyz(container: Container = Depends(get_container)) -> JSONResponse:
        # Readiness: can we reach our dependencies?
        checks = await container.check_readiness()
        ready = all(checks.values())
        return JSONResponse(
            status_code=200 if ready else 503,
            content={"ready": ready, "checks": checks},
        )

    return app

# Create the FastAPI application
app = create_application()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Scholar RAG Web App!"}

# Run the application
if __name__ == "__main__":
    run(app, host="127.0.0.1", port=int(os.getenv("FASTAPI_PORT", 8000)))