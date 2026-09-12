"""Server-side EV ownership authorization for the Driver role (P3).

The authenticated principal — never a client-supplied ev_id alone — is what
determines which EV a driver is allowed to see or act on. Every driver
service function must resolve its EV through `get_authorized_ev` instead of
loading an EV directly by a caller-supplied id.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.auth import Principal
from app.models.ev import EV


class EVAccessDeniedError(Exception):
    """Raised when an authenticated driver requests an EV they do not own.

    Deliberately used both when the requested EV belongs to someone else and
    when it does not exist at all, so the response never reveals whether a
    given EV id exists in the system.
    """


def get_authorized_ev(db: Session, principal: Principal, ev_id: str | None = None) -> EV:
    """Resolve the EV an authenticated driver is authorized to act on.

    - The EV bound to this driver's account (owner_user_id == principal.user_id)
      is always the source of truth.
    - If the caller also supplies an ev_id (e.g. via query param), it must
      match that owned EV's id, or the request is rejected.
    - If no EV is bound to this driver account at all, raises LookupError so
      the API layer can return a 404 distinguishing "not configured" from
      "not authorized".
    """
    owned = db.query(EV).filter(EV.owner_user_id == principal.user_id).first()
    if owned is None:
        raise LookupError(
            "No EV is assigned to this driver account. An operator must bind an EV first."
        )
    if ev_id is not None and ev_id != owned.id:
        raise EVAccessDeniedError(
            f"Driver {principal.user_id} is not authorized to access EV {ev_id}."
        )
    return owned