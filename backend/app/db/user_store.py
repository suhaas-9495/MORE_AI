# backend/app/db/user_store.py
from typing import Dict, Optional
from backend.app.core.security import hash_password

# in-memory store — swapped for real DB on Day 6
_users: Dict[str, dict] = {}


def create_user(username: str, password: str) -> dict:
    if username in _users:
        raise ValueError("Username already exists")
    user = {
        "username": username,
        "hashed_password": hash_password(password),
        "is_active": True,
    }
    _users[username] = user
    return user


def get_user(username: str) -> Optional[dict]:
    return _users.get(username)