"""Common/shared schemas."""

from typing import Optional, List, Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    code: str
    message: str
    message_ar: Optional[str] = None
    details: Optional[List[ErrorDetail]] = None


class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    pages: int


class PaginatedResponse(BaseModel):
    data: List[Any]
    meta: PaginationMeta


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
