from typing import Any

from pydantic import BaseModel


class ErrorRead(BaseModel):
    detail: str
    code: str


class HealthRead(BaseModel):
    status: str
    app: str
    version: str


Responses = dict[int | str, dict[str, Any]]

UNAUTHORIZED: Responses = {401: {"model": ErrorRead, "description": "Missing or wrong X-API-Key"}}
NOT_AUTHENTICATED: Responses = {
    401: {"model": ErrorRead, "description": "Missing or invalid access token"}
}
INVALID_LOGIN: Responses = {401: {"model": ErrorRead, "description": "Wrong e-mail or password"}}
NOT_FOUND: Responses = {404: {"model": ErrorRead, "description": "Not found"}}
CONFLICT: Responses = {409: {"model": ErrorRead, "description": "Conflict"}}
