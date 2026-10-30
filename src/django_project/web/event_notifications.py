"""Opt out of outbound creation/change notifications for controlled imports."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_notifications_suppressed: ContextVar[bool] = ContextVar("event_notifications_suppressed", default=False)


def event_notifications_suppressed() -> bool:
    return _notifications_suppressed.get()


@contextmanager
def suppress_event_notifications() -> Iterator[None]:
    token = _notifications_suppressed.set(True)
    try:
        yield
    finally:
        _notifications_suppressed.reset(token)
