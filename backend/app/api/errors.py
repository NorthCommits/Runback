import json
from collections.abc import Sequence
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.services.ingestion import IngestionError


def correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", str(uuid4()))


def install_error_handlers(application: FastAPI) -> None:
    @application.exception_handler(IngestionError)
    async def handle_ingestion_error(request: Request, error: IngestionError) -> JSONResponse:
        return error_response(request, error.status_code, error.code, error.detail)

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        return error_response(
            request,
            422,
            "validation_error",
            "The request body does not match the ingestion contract",
            {"errors": encode_validation_errors(error.errors())},
        )


def error_response(
    request: Request,
    status_code: int,
    code: str,
    detail: str,
    extra: dict[str, object] | None = None,
) -> JSONResponse:
    content: dict[str, object] = {
        "code": code,
        "detail": detail,
        "correlation_id": correlation_id(request),
    }
    if extra is not None:
        content.update(extra)
    return JSONResponse(
        status_code=status_code,
        content=json.loads(json.dumps(content, default=str)),
    )


def encode_validation_errors(errors: Sequence[Any]) -> list[dict[str, Any]]:
    encoded_errors: list[dict[str, Any]] = []
    for error in errors:
        encoded_errors.append(
            {
                "loc": list(error.get("loc", [])),
                "message": str(error.get("msg", "Invalid value")),
                "type": str(error.get("type", "validation_error")),
            }
        )
    return encoded_errors
