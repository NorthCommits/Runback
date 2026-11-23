from typing import Annotated

from fastapi import APIRouter, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.ingestion import TraceBatchInput, TraceBatchResponse
from app.services.ingestion import TraceIngestionService

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/traces", response_model=TraceBatchResponse, status_code=202)
async def ingest_traces(
    request: Request,
    batch: TraceBatchInput,
    authorization: Annotated[str | None, Header()] = None,
) -> TraceBatchResponse:
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        service = TraceIngestionService(
            session=session,
            sensitive_keys=request.app.state.settings.ingest_redaction_keys,
            max_payload_bytes=request.app.state.settings.ingest_max_payload_bytes,
            payload_store=request.app.state.payload_store,
        )
        return await service.ingest(authorization, batch)
