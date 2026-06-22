"""Global error handling middleware."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        details.append({"field": field, "message": error["msg"]})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "message_ar": "فشل التحقق من البيانات",
                "details": details,
            }
        },
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors (unique constraint violations, etc.)."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": {
                "code": "DUPLICATE_ENTRY",
                "message": "A record with this data already exists",
                "message_ar": "يوجد سجل بهذه البيانات بالفعل",
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "message_ar": "حدث خطأ داخلي",
            }
        },
    )
