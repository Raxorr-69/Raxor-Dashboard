import datetime
import secrets

import jwt

from core.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET_KEY


def new_session_id() -> str:
    """A fresh, random id for a new row in db/sessions.py's
    dashboard_sessions table."""

    return secrets.token_urlsafe(32)


def session_expiry() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=JWT_EXPIRE_MINUTES
    )


def mint_session_jwt(session_id: str) -> str:
    """Sign a JWT that references a session stored in Postgres (see
    db/sessions.py) by id — the JWT itself carries no session data, just
    a pointer, so deleting the row (logout) or the row's own
    expires_at invalidates it immediately regardless of the JWT's own
    exp claim."""

    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sid": session_id,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_session_jwt(token: str) -> dict:
    """Decode and validate a session token, returning its payload
    (just {"sid": ..., "iat": ..., "exp": ...}).

    Raises jwt.PyJWTError (or a subclass) if the token is invalid or expired.
    """

    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


# =========================
# One-time login codes
# =========================
#
# The OAuth redirect from Discord (see api/routes/auth.py's /callback)
# is a plain browser GET, so it can only ever hand the frontend
# something through the URL. Putting the actual session JWT there would
# mean it lands in browser history, and potentially in server/proxy
# access logs — exactly the kind of long-lived bearer credential that
# shouldn't sit in a URL.
#
# Instead, /callback mints one of THESE — a random, single-use,
# short-lived code — and puts that in the redirect URL. The frontend
# immediately exchanges it for the real JWT via a POST body
# (see /auth/exchange), and the code is consumed the instant it's used
# (or expires on its own after LOGIN_CODE_TTL_SECONDS either way), so
# even if it did leak into a log line, it's already useless.
#
# In-memory and not persisted to Postgres like the session store is:
# these live for at most a few seconds between the redirect landing and
# the frontend's exchange call, so there's no real correctness cost to
# losing a handful of them on a restart — the rare unlucky user just
# clicks "log in" again.

LOGIN_CODE_TTL_SECONDS = 60
_LOGIN_CODES: dict[str, tuple[str, datetime.datetime]] = {}


def create_login_code(session_id: str) -> str:
    code = secrets.token_urlsafe(32)
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        seconds=LOGIN_CODE_TTL_SECONDS
    )
    _LOGIN_CODES[code] = (session_id, expires_at)
    return code


def consume_login_code(code: str) -> str | None:
    """One-time read: pops and returns the session id, or None if the
    code was never valid, was already used, or has expired."""

    entry = _LOGIN_CODES.pop(code, None)
    if entry is None:
        return None

    session_id, expires_at = entry
    if datetime.datetime.now(datetime.timezone.utc) > expires_at:
        return None

    return session_id
