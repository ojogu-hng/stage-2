from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.log import setup_logger

# Set up logger
exception_logger = setup_logger(__name__, "error.log")


# Custom Exception Classes


class BaseExceptionClass(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(BaseExceptionClass):
    pass


class AlreadyExist(BaseExceptionClass):
    pass

class ServiceUnavailableError(BaseExceptionClass):
    pass


def register_error_handler(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        exception_logger.error(f"HTTP {exc.status_code}: {exc.detail}")
        return JSONResponse(
            content={"error": exc.detail},
            status_code=exc.status_code,
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_error_handler(request: Request, exc: ValidationError):
        exception_logger.error(f"Pydantic validation error: {str(exc)}")
        return JSONResponse(
            content={"error": "Validation error", "details": exc.errors()},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    @app.exception_handler(RequestValidationError)
    async def bad_request_error_handler(request: Request, exc: RequestValidationError):
        exception_logger.error(f"Bad request error: {str(exc)}")
        return JSONResponse(
            content={
                "error": "Invalid request parameters",
                "errors": exc.errors(),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(request: Request, exc: NotFoundError):
        exception_logger.error(f"Not found error: {str(exc)}")
        return JSONResponse(
            content={
                "error": str(exc.message) or "Not found"
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    @app.exception_handler(AlreadyExist)
    async def already_exist_error_handler(request: Request, exc: AlreadyExist):
        exception_logger.error(f"Already exists error: {str(exc)}")
        return JSONResponse(
            content={
                "error": str(exc.message) or "Resource already exists"
            },
            status_code=status.HTTP_409_CONFLICT,
        )

    @app.exception_handler(ServiceUnavailableError)
    async def service_unavailable_error_handler(request: Request, exc: ServiceUnavailableError):
        exception_logger.error(f"Service unavailable error: {str(exc)}")
        return JSONResponse(
            content={
                "error": "External data source unavailable",
                "details": str(exc.message)
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
