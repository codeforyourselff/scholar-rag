import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from app.api.schemas.errors import ErrorResponseModel, ValidationErrorDetail, ValidationErrorDetail
from app.domain.exception import PortUnavailibleError

logging.basicConfig(level=logging.ERROR)

def register_exception_handlers(app:FastAPI)-> None:
    @app.exception_handler(PortUnavailibleError)
    async def port_unavailable_exception_handler(request: Request, exc: PortUnavailibleError):
        return JSONResponse(
            status_code=503,
            content=ErrorResponseModel(
                status_code=503,
                error_code="PORT_UNAVAILABLE",
                details=None
            ).model_dump(exclude_none=True)
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logging.error(f"Unhandled exception caught by global filter: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ErrorResponseModel(
                status_code=500,
                error_code="INTERNAL_SERVER_ERROR",
                details=None
            ).model_dump(exclude_none=True)
        )
    
    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=ErrorResponseModel(
                status_code=422,
                error_code="VALIDATION_ERROR",
                details=[ValidationErrorDetail(loc=error['loc'], msg=error['msg'], type=error['type']) for error in exc.errors()]
            ).model_dump(exclude_none=True)
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponseModel(
                status_code=exc.status_code,
                error_code="HTTP_EXCEPTION",
                details=None
            ).model_dump(exclude_none=True)
        )