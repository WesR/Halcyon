import pytest
from unittest.mock import Mock, AsyncMock
from halcyon.events import (Event, MemberEvent, ReactionEvent, RedactionEvent,
                            StickerEvent, TypingEvent, ReceiptEvent,
                            PresenceEvent, AccountDataEvent)
from halcyon.halcyon import Client


class TestEvent:
    """Test the base Event model"""

    def test_event_from_raw(self):
        raw = {
            "type": "m.room.name",
            "sender": "@alice:matrix.org",
            "origin_server_ts": 1700000000000,
            "event_id": "$ev1",
            "state_key": "",
            "content": {"name": "New Name"},
            "unsigned": {"age": 100},
        }
        ev = Event(raw, room_id="!room:matrix.org", source="state")

        assert ev.type == "m.room.name"
        assert ev.sender == "@alice:matrix.org"
        assert ev.origin_server_ts == 1700000000000
        assert ev.event_id == "$ev1"
        assert ev.room_id == "!room:matrix.org"
        assert ev.state_key == ""
        assert ev.content == {"name": "New Name"}
        assert ev.unsigned == {"age": 100}
        assert ev.source == "state"
        assert ev._raw == raw
        assert bool(ev) is True

    def test_event_empty(self):
        ev = Event()
        assert bool(ev) is False
        assert ev.type is None

    def test_event_minimal(self):
        raw = {"type": "m.unknown", "content": {}}
        ev = Event(raw)
        assert ev.type == "m.unknown"
        assert ev.sender is None
        assert ev.event_id is None


class TestOnEventHook:
    """Test on_event dispatch through the sync pipeline"""

    def _make_sync_response(self, **kwargs):
        resp = {"next_batch": "s1234"}
        resp.update(kwargs)
        return resp

    @pytest.mark.asyncio
    async def test_on_event_fires_for_timeline(self):
        client = Client()
        client.restrunner = Mock()
        client.roomCache = {"rooms": {}}
        client.restrunner.getRoomState.return_value = []
        received = []

        @client.event
        async def on_event(ev):
            received.append(ev)

        sync_resp = self._make_sync_response(rooms={
            "join": {
                "!room:matrix.org": {
                    "timeline": {
                        "events": [{
                            "type": "m.room.message",
                            "sender": "@a:m.org",
                            "content": {"msgtype": "m.text", "body": "hi"},
                            "origin_server_ts": 1000,
                            "event_id": "$m1"
                        }]
                    }
                }
            }
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
        assert len(received) == 1
        assert received[0].type == "m.room.message"
        assert received[0].source == "timeline"
        assert received[0].room_id == "!room:matrix.org"

    @pytest.mark.asyncio
    async def test_on_event_fires_for_state(self):
        client = Client()
        client.restrunner = Mock()
        client.roomCache = {"rooms": {}}
        client.restrunner.getRoomState.return_value = []
        received = []

        @client.event
        async def on_event(ev):
            received.append(ev)

        sync_resp = self._make_sync_response(rooms={
            "join": {
                "!room:matrix.org": {
                    "state": {
                        "events": [{"type": "m.room.topic", "content": {"topic": "Hi"}}]
                    }
                }
            }
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
        assert len(received) == 1
        assert received[0].type == "m.room.topic"
        assert received[0].source == "state"

    @pytest.mark.asyncio
    async def test_on_event_fires_for_presence(self):
        client = Client()
        client.restrunner = Mock()
        received = []

        @client.event
        async def on_event(ev):
            received.append(ev)

        sync_resp = self._make_sync_response(presence={
            "events": [{
                "type": "m.presence",
                "sender": "@bob:matrix.org",
                "content": {"presence": "online"}
            }]
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
        assert len(received) == 1
        assert received[0].type == "m.presence"
        assert received[0].source == "presence"

    @pytest.mark.asyncio
    async def test_on_event_fires_for_ephemeral(self):
        client = Client()
        client.restrunner = Mock()
        client.roomCache = {"rooms": {}}
        received = []

        @client.event
        async def on_event(ev):
            received.append(ev)

        sync_resp = self._make_sync_response(rooms={
            "join": {
                "!room:matrix.org": {
                    "ephemeral": {
                        "events": [{"type": "m.typing", "content": {"user_ids": ["@a:m.org"]}}]
                    }
                }
            }
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
        assert len(received) == 1
        assert received[0].type == "m.typing"
        assert received[0].source == "ephemeral"

    @pytest.mark.asyncio
    async def test_on_event_and_typed_hook_both_fire(self):
        """on_message and on_event should both fire for m.room.message"""
        client = Client()
        client.restrunner = Mock()
        client.roomCache = {"rooms": {}}
        client.restrunner.getRoomState.return_value = []
        messages = []
        events = []

        @client.event
        async def on_message(msg):
            messages.append(msg)

        @client.event
        async def on_event(ev):
            events.append(ev)

        sync_resp = self._make_sync_response(rooms={
            "join": {
                "!room:matrix.org": {
                    "timeline": {
                        "events": [{
                            "type": "m.room.message",
                            "sender": "@a:m.org",
                            "content": {"msgtype": "m.text", "body": "hi"},
                            "origin_server_ts": 1000,
                            "event_id": "$m1"
                        }]
                    }
                }
            }
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
        assert len(messages) == 1
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_unsupported_event_still_fires_on_event(self):
        """Unknown event types should still be observable via on_event"""
        client = Client()
        client.restrunner = Mock()
        client.roomCache = {"rooms": {}}
        received = []

        @client.event
        async def on_event(ev):
            received.append(ev)

        sync_resp = self._make_sync_response(rooms={
            "join": {
                "!room:matrix.org": {
                    "timeline": {
                        "events": [{
                            "type": "org.custom.unsupported",
                            "sender": "@a:m.org",
                            "content": {"data": "payload"},
                            "origin_server_ts": 1000,
                            "event_id": "$u1"
                        }]
                    }
                }
            }
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
        assert len(received) == 1
        assert received[0].type == "org.custom.unsupported"
        assert received[0].content == {"data": "payload"}


class TestMemberEvent:
    """Test the MemberEvent typed wrapper"""

    def test_member_join(self):
        raw = {
            "type": "m.room.member",
            "sender": "@alice:m.org",
            "state_key": "@alice:m.org",
            "event_id": "$ev1",
            "origin_server_ts": 1000,
            "content": {
                "membership": "join",
                "displayname": "Alice",
                "avatar_url": "mxc://m.org/avatar",
                "is_direct": False,
            }
        }
        ev = MemberEvent(raw, room_id="!r:m.org")
        assert ev.membership == "join"
        assert ev.displayname == "Alice"
        assert ev.avatar_url == "mxc://m.org/avatar"
        assert ev.is_direct is False
        assert ev.state_key == "@alice:m.org"

    def test_member_ban_with_reason(self):
        raw = {
            "type": "m.room.member",
            "sender": "@admin:m.org",
            "state_key": "@bad:m.org",
            "content": {"membership": "ban", "reason": "spam"}
        }
        ev = MemberEvent(raw, room_id="!r:m.org")
        assert ev.membership == "ban"
        assert ev.reason == "spam"

    def test_member_knock(self):
        raw = {
            "type": "m.room.member",
            "sender": "@bob:m.org",
            "state_key": "@bob:m.org",
            "content": {"membership": "knock", "reason": "Please let me in"}
        }
        ev = MemberEvent(raw, room_id="!r:m.org")
        assert ev.membership == "knock"
        assert ev.reason == "Please let me in"

    def test_member_third_party_invite(self):
        raw = {
            "type": "m.room.member",
            "sender": "@server:m.org",
            "state_key": "@ext:m.org",
            "content": {
                "membership": "invite",
                "third_party_invite": {"display_name": "ext@example.com"},
                "join_authorised_via_users_server": "@admin:m.org",
            }
        }
        ev = MemberEvent(raw, room_id="!r:m.org")
        assert ev.membership == "invite"
        assert ev.third_party_invite["display_name"] == "ext@example.com"
        assert ev.join_authorised_via_users_server == "@admin:m.org"


class TestReactionEvent:
    def test_reaction(self):
        raw = {
            "type": "m.reaction",
            "sender": "@alice:m.org",
            "event_id": "$react1",
            "origin_server_ts": 2000,
            "content": {
                "m.relates_to": {
                    "rel_type": "m.annotation",
                    "event_id": "$target_msg",
                    "key": "👍"
                }
            }
        }
        ev = ReactionEvent(raw, room_id="!r:m.org")
        assert ev.reaction_key == "👍"
        assert ev.relates_to_event_id == "$target_msg"
        assert ev.sender == "@alice:m.org"


class TestRedactionEvent:
    def test_redaction(self):
        raw = {
            "type": "m.room.redaction",
            "sender": "@mod:m.org",
            "event_id": "$redact1",
            "origin_server_ts": 3000,
            "redacts": "$bad_event",
            "content": {"reason": "inappropriate"}
        }
        ev = RedactionEvent(raw, room_id="!r:m.org")
        assert ev.redacts == "$bad_event"
        assert ev.reason == "inappropriate"
        assert ev.sender == "@mod:m.org"

    def test_redaction_no_reason(self):
        raw = {
            "type": "m.room.redaction",
            "sender": "@mod:m.org",
            "redacts": "$ev",
            "content": {}
        }
        ev = RedactionEvent(raw, room_id="!r:m.org")
        assert ev.redacts == "$ev"
        assert ev.reason is None


class TestStickerEvent:
    def test_sticker(self):
        raw = {
            "type": "m.sticker",
            "sender": "@alice:m.org",
            "event_id": "$sticker1",
            "origin_server_ts": 4000,
            "content": {
                "body": "smiley",
                "url": "mxc://m.org/sticker123",
                "info": {
                    "mimetype": "image/png",
                    "w": 128,
                    "h": 128,
                    "size": 5000,
                    "thumbnail_url": "mxc://m.org/thumb",
                    "thumbnail_info": {"w": 64, "h": 64}
                }
            }
        }
        ev = StickerEvent(raw, room_id="!r:m.org")
        assert ev.body == "smiley"
        assert ev.url == "mxc://m.org/sticker123"
        assert ev.info["w"] == 128
        assert ev.thumbnail_url == "mxc://m.org/thumb"
        assert ev.thumbnail_info["w"] == 64


class TestTypingEvent:
    def test_typing(self):
        raw = {
            "type": "m.typing",
            "content": {"user_ids": ["@alice:m.org", "@bob:m.org"]}
        }
        ev = TypingEvent(raw, room_id="!r:m.org")
        assert ev.user_ids == ["@alice:m.org", "@bob:m.org"]
        assert ev.source == "ephemeral"

    def test_typing_empty(self):
        raw = {"type": "m.typing", "content": {"user_ids": []}}
        ev = TypingEvent(raw, room_id="!r:m.org")
        assert ev.user_ids == []


class TestReceiptEvent:
    def test_receipt(self):
        raw = {
            "type": "m.receipt",
            "content": {
                "$event_id": {
                    "m.read": {
                        "@alice:m.org": {"ts": 1000}
                    }
                }
            }
        }
        ev = ReceiptEvent(raw, room_id="!r:m.org")
        assert ev.receipts is not None
        assert "$event_id" in ev.receipts
        assert ev.source == "ephemeral"


class TestPresenceEvent:
    def test_presence(self):
        raw = {
            "type": "m.presence",
            "sender": "@alice:m.org",
            "content": {
                "presence": "online",
                "currently_active": True,
                "last_active_ago": 5000,
                "status_msg": "Working",
                "avatar_url": "mxc://m.org/avatar",
                "displayname": "Alice"
            }
        }
        ev = PresenceEvent(raw)
        assert ev.presence == "online"
        assert ev.currently_active is True
        assert ev.last_active_ago == 5000
        assert ev.status_msg == "Working"
        assert ev.user_avatar_url == "mxc://m.org/avatar"
        assert ev.user_displayname == "Alice"
        assert ev.source == "presence"


class TestTypedDispatch:
    """Test that the pipeline dispatches typed events to the right hooks"""

    def _sync(self, **kwargs):
        resp = {"next_batch": "s1"}
        resp.update(kwargs)
        return resp

    @pytest.mark.asyncio
    async def test_reaction_dispatch(self):
        client = Client()
        client.restrunner = Mock()
        client.roomCache = {"rooms": {}}
        received = []

        @client.event
        async def on_reaction(ev):
            received.append(ev)

        sync = self._sync(rooms={"join": {"!r:m.org": {"timeline": {"events": [{
            "type": "m.reaction",
            "sender": "@a:m.org",
            "event_id": "$r1",
            "content": {"m.relates_to": {"rel_type": "m.annotation", "event_id": "$t", "key": "🎉"}}
        }]}}}})

        client.restrunner.sync_async = AsyncMock(return_value=sync)
        client.firstSync = False
        await client._homeserverSync()

        assert len(received) == 1
        assert isinstance(received[0], ReactionEvent)
        assert received[0].reaction_key == "🎉"

    @pytest.mark.asyncio
    async def test_redaction_dispatch(self):
        client = Client()
        client.restrunner = Mock()
        client.roomCache = {"rooms": {}}
        received = []

        @client.event
        async def on_redaction(ev):
            received.append(ev)

        sync = self._sync(rooms={"join": {"!r:m.org": {"timeline": {"events": [{
            "type": "m.room.redaction",
            "sender": "@mod:m.org",
            "event_id": "$rd1",
            "redacts": "$bad",
            "content": {"reason": "spam"}
        }]}}}})

        client.restrunner.sync_async = AsyncMock(return_value=sync)
        client.firstSync = False
        await client._homeserverSync()

        assert len(received) == 1
        assert isinstance(received[0], RedactionEvent)
        assert received[0].redacts == "$bad"

    @pytest.mark.asyncio
    async def test_member_dispatch_from_timeline(self):
        client = Client()
        client.restrunner = Mock()
        client.roomCache = {"rooms": {}}
        client.restrunner.getRoomState.return_value = []
        received = []

        @client.event
        async def on_room_member(ev):
            received.append(ev)

        sync = self._sync(rooms={"join": {"!r:m.org": {"timeline": {"events": [{
            "type": "m.room.member",
            "sender": "@alice:m.org",
            "state_key": "@alice:m.org",
            "content": {"membership": "join", "displayname": "Alice"}
        }]}}}})

        client.restrunner.sync_async = AsyncMock(return_value=sync)
        client.firstSync = False
        await client._homeserverSync()

        assert len(received) == 1
        assert isinstance(received[0], MemberEvent)
        assert received[0].membership == "join"

    @pytest.mark.asyncio
    async def test_member_dispatch_from_state(self):
        client = Client()
        client.restrunner = Mock()
        client.roomCache = {"rooms": {}}
        client.restrunner.getRoomState.return_value = []
        received = []

        @client.event
        async def on_room_member(ev):
            received.append(ev)

        sync = self._sync(rooms={"join": {"!r:m.org": {"state": {"events": [{
            "type": "m.room.member",
            "sender": "@bob:m.org",
            "state_key": "@bob:m.org",
            "content": {"membership": "leave"}
        }]}}}})

        client.restrunner.sync_async = AsyncMock(return_value=sync)
        client.firstSync = False
        await client._homeserverSync()

        assert len(received) == 1
        assert received[0].membership == "leave"
