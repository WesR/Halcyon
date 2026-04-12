import pytest
from unittest.mock import Mock, AsyncMock
from halcyon.events import Event
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
