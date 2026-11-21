from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.core.config import Settings, get_settings
from app.schemas.dataset import DatasetSessionResponse, DeleteSessionResponse
from app.services.csv_parser import CSVParseError, parse_csv_bytes
from app.services.profiler import build_dataset_profile
from app.services.session_store import (
    EphemeralSessionStore,
    SessionMeta,
    SessionNotFoundError,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])

SAMPLE_CSV_PATH = Path(__file__).resolve().parents[2] / "sample_data" / "orders_sample.csv"

PRIVACY_NOTICE = (
    "AskGrid sends only column names and inferred data types (never raw row values) "
    "to the AI model. Uploaded files are temporary and auto-delete after session expiry "
    "or immediately when you click Delete."
)


def get_session_store(
    settings: Annotated[Settings, Depends(get_settings)],
) -> EphemeralSessionStore:
    return EphemeralSessionStore(
        base_dir=Path(settings.session_storage_dir),
        ttl_minutes=settings.session_ttl_minutes,
    )


def _to_response(meta: SessionMeta) -> DatasetSessionResponse:
    return DatasetSessionResponse(
        session_id=meta.session_id,
        filename=meta.filename,
        is_sample=meta.is_sample,
        expires_at=meta.expires_at,
        privacy_notice=PRIVACY_NOTICE,
        profile=meta.profile,
    )


@router.post(
    "/upload",
    response_model=DatasetSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    file: UploadFile,
    settings: Annotated[Settings, Depends(get_settings)],
    store: Annotated[EphemeralSessionStore, Depends(get_session_store)],
) -> DatasetSessionResponse:
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    # Streaming size guard: never read an unbounded file into RAM
    raw_bytes = await file.read(max_bytes + 1)
    if len(raw_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.max_upload_size_mb} MB.",
        )

    try:
        parsed = parse_csv_bytes(
            raw_bytes,
            max_size_mb=settings.max_upload_size_mb,
            max_rows=settings.max_rows,
            max_columns=settings.max_columns,
        )
    except CSVParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    profile = build_dataset_profile(parsed)
    meta = store.create_session(raw_bytes, profile, filename=file.filename, is_sample=False)
    return _to_response(meta)


@router.post(
    "/sample",
    response_model=DatasetSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def load_sample_dataset(
    settings: Annotated[Settings, Depends(get_settings)],
    store: Annotated[EphemeralSessionStore, Depends(get_session_store)],
) -> DatasetSessionResponse:
    raw_bytes = SAMPLE_CSV_PATH.read_bytes()
    parsed = parse_csv_bytes(
        raw_bytes,
        max_size_mb=settings.max_upload_size_mb,
        max_rows=settings.max_rows,
        max_columns=settings.max_columns,
    )
    profile = build_dataset_profile(parsed)
    meta = store.create_session(
        raw_bytes,
        profile,
        filename="orders_sample.csv",
        is_sample=True,
    )
    return _to_response(meta)


@router.get("/{session_id}", response_model=DatasetSessionResponse)
def get_dataset_session(
    session_id: str,
    store: Annotated[EphemeralSessionStore, Depends(get_session_store)],
) -> DatasetSessionResponse:
    try:
        meta = store.get_meta(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_response(meta)


@router.delete("/{session_id}", response_model=DeleteSessionResponse)
def delete_dataset_session(
    session_id: str,
    store: Annotated[EphemeralSessionStore, Depends(get_session_store)],
) -> DeleteSessionResponse:
    deleted = store.delete_session(session_id)
    return DeleteSessionResponse(session_id=session_id, deleted=deleted)
