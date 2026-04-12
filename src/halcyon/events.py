"""
Base event models for the Halcyon Matrix client library.

Provides a generic event wrapper so that every sync event -- including
those without a specialized typed model -- is observable by library users.
"""

from pydantic import BaseModel, PrivateAttr
from typing import Optional, Dict, Any
from halcyon.security import get_nested_config


class Event(BaseModel):
    """Generic Matrix event.

    Wraps any event delivered through /sync.  Specialized event types
    (Message, MemberEvent, etc.) carry richer typed fields, but every
    event can also be consumed through this base representation via the
    ``on_event`` callback.
    """
    model_config = get_nested_config()

    type: Optional[str] = None
    sender: Optional[str] = None
    origin_server_ts: Optional[int] = None
    event_id: Optional[str] = None
    room_id: Optional[str] = None
    state_key: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    unsigned: Optional[Dict[str, Any]] = None
    source: Optional[str] = None  # e.g. "timeline", "state", "ephemeral", "presence", "account_data"
    _raw: Optional[Dict[str, Any]] = PrivateAttr(default_factory=dict)

    def __init__(self, raw_event: Optional[Dict[str, Any]] = None,
                 room_id: Optional[str] = None,
                 source: Optional[str] = None, **kwargs):
        if raw_event:
            super().__init__(
                type=raw_event.get("type"),
                sender=raw_event.get("sender"),
                origin_server_ts=raw_event.get("origin_server_ts"),
                event_id=raw_event.get("event_id"),
                room_id=room_id or raw_event.get("room_id"),
                state_key=raw_event.get("state_key"),
                content=raw_event.get("content"),
                unsigned=raw_event.get("unsigned"),
                source=source,
                **kwargs
            )
            self._raw = raw_event
        else:
            super().__init__(room_id=room_id, source=source, **kwargs)
            self._raw = {}

    def __bool__(self):
        return bool(self._raw)
