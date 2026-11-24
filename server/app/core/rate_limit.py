import time
from collections import defaultdict, deque
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings


class SlidingWindowRateLimiter:
    """Lightweight in-memory per-IP sliding-window rate limiter (zero external deps)."""

    def __init__(
        self,
        max_requests: int,
        window_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds) for the given client key."""
        now = self._clock()
        bucket = self._hits[key]
        cutoff = now - self._window_seconds

        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

        if len(bucket) >= self._max_requests:
            retry_after = max(1, int(self._window_seconds - (now - bucket[0])) + 1)
            return False, retry_after

        bucket.append(now)
        return True, 0

    def clear(self) -> None:
        self._hits.clear()


def get_client_ip(request: Request) -> str:
    """Extract client IP safely behind reverse proxies like Render / Cloudflare."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


_upload_limiter: SlidingWindowRateLimiter | None = None
_ask_limiter: SlidingWindowRateLimiter | None = None


def limit_upload_requests(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """FastAPI dependency enforcing per-IP upload/sample rate limits."""
    global _upload_limiter
    if not settings.rate_limit_enabled:
        return
    if _upload_limiter is None:
        _upload_limiter = SlidingWindowRateLimiter(settings.rate_limit_upload_per_min)
    allowed, retry_after = _upload_limiter.check(get_client_ip(request))
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many uploads. Please wait a minute before trying again.",
            headers={"Retry-After": str(retry_after)},
        )


def limit_ask_requests(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """FastAPI dependency enforcing per-IP question rate limits."""
    global _ask_limiter
    if not settings.rate_limit_enabled:
        return
    if _ask_limiter is None:
        _ask_limiter = SlidingWindowRateLimiter(settings.rate_limit_ask_per_min)
    allowed, retry_after = _ask_limiter.check(get_client_ip(request))
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many questions in a short time. Please wait a moment.",
            headers={"Retry-After": str(retry_after)},
        )
