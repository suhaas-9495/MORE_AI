# backend/app/db/user_store.py
from typing import Dict, Optional
from backend.app.core.security import hash_password
from backend.app.core.rbac import Role
# in-memory store — swapped for real DB on Day 6
_users: Dict[str, dict] = {}


def create_user(username: str, password: str, role: Role = Role.DEVELOPER) -> dict:
    if username in _users:
        raise ValueError("Username already exists")
    user = {
        "username": username,
        "hashed_password": hash_password(password),
        "is_active": True,
        "role": role,  
    }
    _users[username] = user
    return user


def get_user(username: str) -> Optional[dict]:
    return _users.get(username)

def update_role(username: str, role: str) -> bool:
    if username not in _users:
        return False
    _users[username]["role"] = role
    return True
