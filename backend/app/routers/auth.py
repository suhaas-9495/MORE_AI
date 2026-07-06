from fastapi import APIRouter, HTTPException, Depends, status
from backend.app.models.schemas import UserRegister, UserLogin, Token, UserOut
from backend.app.db.user_store import create_user, get_user
from backend.app.core.security import verify_password, create_access_token
from backend.app.core.dependencies import get_current_user
from backend.app.core.audit import log_audit_event
from backend.app.core.rbac import Role

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserRegister):
    try:
        user = create_user(payload.username, payload.password, role=Role.DEVELOPER)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    log_audit_event(action="auth:register", user=payload.username, resource="auth")
    return UserOut(username=user["username"])


@router.post("/login", response_model=Token)
def login(payload: UserLogin):
    user = get_user(payload.username)
    if not user or not verify_password(payload.password, user["hashed_password"]):
        log_audit_event(
            action="auth:login", user=payload.username,
            resource="auth", status="failed",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    log_audit_event(action="auth:login", user=payload.username, resource="auth")
    token = create_access_token({"sub": payload.username})
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    return UserOut(username=current_user["username"])


@router.get("/audit-logs", tags=["admin"])
async def get_audit_logs(current_user: dict = Depends(get_current_user)):
    from backend.app.core.audit import get_audit_logs
    from backend.app.core.rbac import require_permission
    return get_audit_logs(limit=100)
