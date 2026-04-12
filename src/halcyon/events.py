"""
Event models for the Halcyon Matrix client library.

Provides a generic event wrapper and specialized typed wrappers for
common Matrix event families.
"""

from pydantic import BaseModel, PrivateAttr
from typing import Optional, Dict, Any, List
from halcyon.security import get_nested_config, get_message_config


class Event(BaseModel):
    """Generic Matrix event.

    Wraps any event delivered through /sync.  Specialized event types
    (Message, MemberEvent, etc.) carry richer typed fields, but every
    event can also be consumed through this base representation via the
    ``on_event`` callback.
    """
    model_config = get_message_config()

    type: Optional[str] = None
    sender: Optional[str] = None
    origin_server_ts: Optional[int] = None
    event_id: Optional[str] = None
    room_id: Optional[str] = None
    state_key: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    unsigned: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    sender_user: Optional[Any] = None  # User object when available
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


class MemberEvent(Event):
    """Typed wrapper for m.room.member events."""

    membership: Optional[str] = None
    displayname: Optional[str] = None
    avatar_url: Optional[str] = None
    is_direct: Optional[bool] = None
    reason: Optional[str] = None
    third_party_invite: Optional[Dict[str, Any]] = None
    join_authorised_via_users_server: Optional[str] = None

    def __init__(self, raw_event: Optional[Dict[str, Any]] = None,
                 room_id: Optional[str] = None,
                 source: Optional[str] = None, **kwargs):
        content = (raw_event or {}).get("content", {})
        super().__init__(
            raw_event=raw_event,
            room_id=room_id,
            source=source,
            membership=content.get("membership"),
            displayname=content.get("displayname"),
            avatar_url=content.get("avatar_url"),
            is_direct=content.get("is_direct"),
            reason=content.get("reason"),
            third_party_invite=content.get("third_party_invite"),
            join_authorised_via_users_server=content.get("join_authorised_via_users_server"),
            **kwargs
        )


class ReactionEvent(Event):
    """Typed wrapper for m.reaction events."""

    reaction_key: Optional[str] = None
    relates_to_event_id: Optional[str] = None

    def __init__(self, raw_event: Optional[Dict[str, Any]] = None,
                 room_id: Optional[str] = None,
                 source: Optional[str] = None, **kwargs):
        content = (raw_event or {}).get("content", {})
        relates_to = content.get("m.relates_to", {})
        super().__init__(
            raw_event=raw_event,
            room_id=room_id,
            source=source,
            reaction_key=relates_to.get("key"),
            relates_to_event_id=relates_to.get("event_id"),
            **kwargs
        )


class RedactionEvent(Event):
    """Typed wrapper for m.room.redaction events."""

    redacts: Optional[str] = None
    reason: Optional[str] = None

    def __init__(self, raw_event: Optional[Dict[str, Any]] = None,
                 room_id: Optional[str] = None,
                 source: Optional[str] = None, **kwargs):
        content = (raw_event or {}).get("content", {})
        super().__init__(
            raw_event=raw_event,
            room_id=room_id,
            source=source,
            redacts=raw_event.get("redacts") if raw_event else None,
            reason=content.get("reason"),
            **kwargs
        )


class StickerEvent(Event):
    """Typed wrapper for m.sticker events."""

    body: Optional[str] = None
    url: Optional[str] = None
    info: Optional[Dict[str, Any]] = None

    def __init__(self, raw_event: Optional[Dict[str, Any]] = None,
                 room_id: Optional[str] = None,
                 source: Optional[str] = None, **kwargs):
        content = (raw_event or {}).get("content", {})
        super().__init__(
            raw_event=raw_event,
            room_id=room_id,
            source=source,
            body=content.get("body"),
            url=content.get("url"),
            info=content.get("info"),
            **kwargs
        )

    @property
    def thumbnail_url(self):
        if self.info:
            return self.info.get("thumbnail_url")
        return None

    @property
    def thumbnail_info(self):
        if self.info:
            return self.info.get("thumbnail_info")
        return None


class TypingEvent(Event):
    """Typed wrapper for m.typing ephemeral events."""

    user_ids: List[str] = []

    def __init__(self, raw_event: Optional[Dict[str, Any]] = None,
                 room_id: Optional[str] = None,
                 source: Optional[str] = None, **kwargs):
        content = (raw_event or {}).get("content", {})
        super().__init__(
            raw_event=raw_event,
            room_id=room_id,
            source=source or "ephemeral",
            user_ids=content.get("user_ids", []),
            **kwargs
        )


class ReceiptEvent(Event):
    """Typed wrapper for m.receipt ephemeral events.

    The content structure maps event_id -> receipt_type -> user_id -> data.
    This wrapper exposes the raw mapping and a helper to iterate receipts.
    """

    receipts: Optional[Dict[str, Any]] = None

    def __init__(self, raw_event: Optional[Dict[str, Any]] = None,
                 room_id: Optional[str] = None,
                 source: Optional[str] = None, **kwargs):
        content = (raw_event or {}).get("content", {})
        super().__init__(
            raw_event=raw_event,
            room_id=room_id,
            source=source or "ephemeral",
            receipts=content,
            **kwargs
        )


class PresenceEvent(Event):
    """Typed wrapper for m.presence events."""

    presence: Optional[str] = None
    currently_active: Optional[bool] = None
    last_active_ago: Optional[int] = None
    status_msg: Optional[str] = None
    user_avatar_url: Optional[str] = None
    user_displayname: Optional[str] = None

    def __init__(self, raw_event: Optional[Dict[str, Any]] = None,
                 room_id: Optional[str] = None,
                 source: Optional[str] = None, **kwargs):
        content = (raw_event or {}).get("content", {})
        super().__init__(
            raw_event=raw_event,
            room_id=room_id,
            source=source or "presence",
            presence=content.get("presence"),
            currently_active=content.get("currently_active"),
            last_active_ago=content.get("last_active_ago"),
            status_msg=content.get("status_msg"),
            user_avatar_url=content.get("avatar_url"),
            user_displayname=content.get("displayname"),
            **kwargs
        )


class AccountDataEvent(Event):
    """Typed wrapper for account data events (room-level or global)."""
    pass
