import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.domain.exception import PortUnavailibleError

logging.basicConfig(level=logging.ERROR)

def register_exception_handlers(app:FastAPI)-> None:
    @app.exception_handler(PortUnavailibleError)
    async def port_unavailable_exception_handler(request: Request, exc: PortUnavailibleError):
        logging.error(f"Port unavailable error occurred: {exc}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"message": "The requested port is unavailable."},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logging.error(f"Unexpected error occurred: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"message": "An unexpected error occurred."},
        )
