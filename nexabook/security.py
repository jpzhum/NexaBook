from __future__ import annotations

import secrets
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


CSRF_KEY = "csrf_token"
USER_KEY = "user"


class LoginLimiter:
    def __init__(self, attempts: int = 5, window_seconds: int = 300) -> None:
        self.attempts = attempts
        self.window = window_seconds
        self.events: dict[str, deque[float]] = defaultdict(deque)

    def allowed(self, identity: str) -> bool:
        now = time.monotonic()
        events = self.events[identity]
        while events and events[0] <= now - self.window:
            events.popleft()
        return len(events) < self.attempts

    def failure(self, identity: str) -> None:
        self.events[identity].append(time.monotonic())

    def success(self, identity: str) -> None:
        self.events.pop(identity, None)


def csrf_token(request: Request) -> str:
    token = request.session.get(CSRF_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[CSRF_KEY] = token
    return token


def verify_csrf(request: Request, supplied: str) -> None:
    expected = request.session.get(CSRF_KEY, "")
    if not expected or not secrets.compare_digest(expected, supplied):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
