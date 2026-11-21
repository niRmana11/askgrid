import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import BaseModel

from app.schemas.dataset import DatasetProfile


class SessionNotFoundError(KeyError):
    """Raised when a session ID is invalid, missing, or expired."""


class SessionMeta(BaseModel):
    """Metadata stored alongside an ephemeral CSV on disk."""

    session_id: str
    filename: str
    is_sample: bool
    expires_at: str
    profile: DatasetProfile


def _validate_session_id(session_id: str) -> str:
    """Ensure session_id is a strict UUIDv4 string (prevents path traversal)."""
    try:
        parsed = uuid.UUID(session_id, version=4)
    except ValueError as exc:
        raise SessionNotFoundError("Dataset session not found.") from exc
    if str(parsed) != session_id:
        raise SessionNotFoundError("Dataset session not found.")
    return session_id


def _sanitize_display_filename(filename: str | None) -> str:
    """Keep only the basename for display; never used as an actual disk path."""
    if not filename:
        return "uploaded.csv"
    clean = Path(filename).name.strip()
    return (clean or "uploaded.csv")[:100]


class EphemeralSessionStore:
    """Disk-backed ephemeral CSV session store (0 MB idle RAM, TTL auto-cleanup)."""

    def __init__(self, base_dir: Path, ttl_minutes: int = 60) -> None:
        self.base_dir = base_dir
        self.ttl_minutes = ttl_minutes
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _csv_path(self, session_id: str) -> Path:
        safe_id = _validate_session_id(session_id)
        return self.base_dir / f"{safe_id}.csv"

    def _meta_path(self, session_id: str) -> Path:
        safe_id = _validate_session_id(session_id)
        return self.base_dir / f"{safe_id}.meta.json"

    def create_session(
        self,
        raw_bytes: bytes,
        profile: DatasetProfile,
        *,
        filename: str | None,
        is_sample: bool = False,
    ) -> SessionMeta:
        self.cleanup_expired()
        session_id = str(uuid.uuid4())
        expires_at = (datetime.now(UTC) + timedelta(minutes=self.ttl_minutes)).isoformat()
        meta = SessionMeta(
            session_id=session_id,
            filename=_sanitize_display_filename(filename),
            is_sample=is_sample,
            expires_at=expires_at,
            profile=profile,
        )
        self._csv_path(session_id).write_bytes(raw_bytes)
        self._meta_path(session_id).write_text(meta.model_dump_json(), encoding="utf-8")
        return meta

    def get_meta(self, session_id: str) -> SessionMeta:
        meta_path = self._meta_path(session_id)
        csv_path = self._csv_path(session_id)
        if not meta_path.exists() or not csv_path.exists():
            raise SessionNotFoundError("Dataset session not found or expired.")

        meta = SessionMeta.model_validate_json(meta_path.read_text(encoding="utf-8"))
        if datetime.fromisoformat(meta.expires_at) <= datetime.now(UTC):
            self.delete_session(session_id)
            raise SessionNotFoundError("Dataset session has expired and was deleted.")
        return meta

    def get_csv_bytes(self, session_id: str) -> bytes:
        """Load raw CSV bytes on demand after validating session TTL."""
        self.get_meta(session_id)
        return self._csv_path(session_id).read_bytes()

    def delete_session(self, session_id: str) -> bool:
        try:
            csv_path = self._csv_path(session_id)
            meta_path = self._meta_path(session_id)
        except SessionNotFoundError:
            return False

        existed = csv_path.exists() or meta_path.exists()
        csv_path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)
        return existed

    def cleanup_expired(self) -> int:
        """Delete all expired session files from the ephemeral directory."""
        removed = 0
        now = datetime.now(UTC)
        for meta_path in self.base_dir.glob("*.meta.json"):
            try:
                meta = SessionMeta.model_validate_json(meta_path.read_text(encoding="utf-8"))
                if datetime.fromisoformat(meta.expires_at) <= now:
                    self.delete_session(meta.session_id)
                    removed += 1
            except Exception:
                meta_path.unlink(missing_ok=True)
        return removed
