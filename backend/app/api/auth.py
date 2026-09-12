"""Authentication endpoints for Aegis."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import authenticate_user, ensure_demo_users, issue_token, get_current_principal, Principal
from app.config import Settings, get_settings
from app.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict[str, str]


class MeResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: str


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    ensure_demo_users(db)
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Email or password is incorrect."}},
        )
    token, expires_in = issue_token(user, settings)
    return LoginResponse(
        access_token=token,
        token_type="Aegis",
        expires_in=expires_in,
        user={"id": user.id, "email": user.email, "display_name": user.display_name, "role": user.role},
    )


@router.get("/me", response_model=MeResponse)
def me(principal: Principal = Depends(get_current_principal)) -> MeResponse:
    return MeResponse(
        id=principal.user_id,
        email=principal.email,
        display_name=principal.display_name,
        role=principal.role,
    )
