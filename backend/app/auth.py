"""Minimal, free, hackathon-grade authentication and RBAC for Aegis.

Passwords are stored as salted PBKDF2-HMAC hashes. Access tokens are signed
short-lived HMAC tokens using only Python's standard library, so the MVP has
no mandatory paid or external identity provider.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models.user import User

ROLE_GRID = "grid_operator"
ROLE_NETWORK = "network_operator"
ROLE_DRIVER = "ev_driver"
ALL_ROLES = {ROLE_GRID, ROLE_NETWORK, ROLE_DRIVER}


@dataclass(frozen=True)
class Principal:
    user_id: str
    email: str
    display_name: str
    role: str
    roles: frozenset[str] | None = None

    def can(self, roles: Iterable[str]) -> bool:
        allowed = set(roles)
        active_roles = self.roles if self.roles is not None else frozenset({self.role})
        return bool(active_roles.intersection(allowed))


DEMO_USERS = (
    {
        "id": "USR-GRID-01",
        "email": "grid@aegis.local",
        "display_name": "Grid Operator",
        "role": ROLE_GRID,
        "password": "AegisGrid26!",
    },
    {
        "id": "USR-NET-01",
        "email": "network@aegis.local",
        "display_name": "Network Operator",
        "role": ROLE_NETWORK,
        "password": "AegisNet26!",
    },
    {
        "id": "USR-DRV-01",
        "email": "driver@aegis.local",
        "display_name": "EV Driver",
        "role": ROLE_DRIVER,
        "password": "AegisDriver26!",
    },
)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 160_000).hex()


def ensure_demo_users(db: Session) -> None:
    for item in DEMO_USERS:
        existing = db.get(User, item["id"])
        if existing:
            continue
        salt = secrets.token_bytes(16)
        db.add(
            User(
                id=item["id"],
                email=item["email"],
                display_name=item["display_name"],
                role=item["role"],
                password_salt=salt.hex(),
                password_hash=_hash_password(item["password"], salt),
            )
        )
    db.commit()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if user is None:
        return None
    expected = _hash_password(password, bytes.fromhex(user.password_salt))
    if not hmac.compare_digest(expected, user.password_hash):
        return None
    return user


def issue_token(user: User, settings: Settings | None = None) -> tuple[str, int]:
    settings = settings or get_settings()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=settings.auth_token_hours)
    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.display_name,
        "role": user.role,
        "exp": int(expires.timestamp()),
    }
    raw = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signature = _b64(hmac.new(settings.auth_secret.encode(), raw.encode(), hashlib.sha256).digest())
    return f"Aegis {raw}.{signature}", int((expires - now).total_seconds())


def decode_token(token: str, settings: Settings | None = None) -> Principal:
    settings = settings or get_settings()
    if not token.startswith("Aegis "):
        raise ValueError("Invalid authentication scheme")
    packed = token[6:].strip()
    try:
        payload_part, sig_part = packed.split(".", 1)
        expected_sig = _b64(
            hmac.new(settings.auth_secret.encode(), payload_part.encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(expected_sig, sig_part):
            raise ValueError("Invalid token signature")
        payload = json.loads(_unb64(payload_part))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("Invalid authentication token") from exc

    try:
        expires_at = int(payload.get("exp", 0))
        user_id = str(payload["sub"])
        email = str(payload["email"])
        display_name = str(payload["name"])
        role = str(payload["role"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid authentication token payload") from exc

    if expires_at < int(datetime.now(timezone.utc).timestamp()):
        raise ValueError("Authentication token expired")
    if role not in ALL_ROLES:
        raise ValueError("Unknown role")

    return Principal(
        user_id=user_id,
        email=email,
        display_name=display_name,
        role=role,
    )


def get_current_principal(
    authorization: str | None = Header(default=None),
) -> Principal:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "AUTH_REQUIRED", "message": "Sign in to access Aegis."}},
            headers={"WWW-Authenticate": "Aegis"},
        )
    try:
        return decode_token(authorization)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": str(exc)}},
            headers={"WWW-Authenticate": "Aegis"},
        ) from exc


def require_role(*roles: str):
    allowed = set(roles)

    def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if not principal.can(allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Your Aegis role is not permitted to perform this action.",
                    }
                },
            )
        return principal

    return dependency


def safe_demo_credentials() -> list[dict[str, str]]:
    """Credentials shown on the local demo login screen only."""
    return [
        {"role": item["role"], "email": item["email"], "password": item["password"]}
        for item in DEMO_USERS
    ]
