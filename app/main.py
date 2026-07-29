# Main entry point for the Scholar RAG Web Application
import os
import uvicorn
import logging
from fastapi import Depends, FastAPI
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.exception import register_exception_handlers
from app.api.routes import document, rag
from app.config import Settings, get_settings
from app.container import Container, get_container
logger = logging.getLogger(__name__)

def inject_container() -> Container:
    return get_container(settings=get_settings())

# manage the lifecycle of external resources (e.g., database connections, background tasks)
@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncIterator[None]:
    # Startup logic here
    settings: Settings = app.state.settings
    container: Container = get_container(settings)
    await container.startup()
    logger.info("Application lifecycle started. Container wired.")
    try:
        yield
    finally:
        await container.shutdown()
        logger.info("Application lifecycle terminated. Resources released.")

# Function to create the FastAPI application

def create_application(settings: Settings) -> FastAPI:
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

    #cors origin for the fastAPI
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app.state.settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # Register global exception handler
    register_exception_handlers(app=app)

    # Router main entry point
    app.include_router(document.router, prefix="/api")
    app.include_router(rag.router, prefix="/api/rag")

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict[str, str]:
        # Liveness: the process is up. Must NOT depend on backends.
        return {"status": "ok"}
    
    @app.get("/readyz", tags=["health"])
    async def readyz(container: Container = Depends(get_container)) -> JSONResponse:
        # Readiness: can we reach our dependencies?
        __checks = await container.check_readiness()
        __ready = all(__checks.values())
        return JSONResponse(
            status_code=200 if __ready else 503,
            content={"ready": __ready, "checks": __checks},
        )

    return app

# Create the FastAPI application
settings: Settings = get_settings()
app: FastAPI = create_application(settings)

# Run the application
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("FASTAPI_PORT", 8000)), reload=settings.environment == "local")