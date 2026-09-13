import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse


# Small, dependency-free rate limiter suitable for a single Render web
# service. It is intentionally conservative on authentication endpoints.
# If you later run multiple dashboard instances, move this to Redis.
_BUCKETS: dict[str, deque[float]] = defaultdict(deque)
_LOCK = Lock()


def client_ip(request: Request) -> str:
    # Render terminates TLS at its proxy. Prefer the first forwarded client
    # address; fall back to the socket peer for local development.
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


def rate_limit(request: Request, *, limit: int, window_seconds: int, scope: str) -> JSONResponse | None:
    now = time.monotonic()
    key = f"{scope}:{client_ip(request)}"
    cutoff = now - window_seconds
    with _LOCK:
        bucket = _BUCKETS[key]
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            retry_after = max(1, int(bucket[0] + window_seconds - now))
            return JSONResponse(
                {"detail": "Too many requests. Please try again later."},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)

    return None


def security_headers(*, production: bool) -> dict[str, str]:
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "base-uri 'self'; frame-ancestors 'none'; object-src 'none'; "
            "script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https://cdn.discordapp.com; "
            "connect-src 'self' https://discord.com https://cdn.discordapp.com; "
            "font-src 'self' data:; form-action 'self' https://discord.com"
        ),
    }
    if production:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return headers
