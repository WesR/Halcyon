import pytest
from unittest.mock import Mock, AsyncMock
from halcyon.user import User
from halcyon.halcyon import Client
from halcyon.room import room


class TestUser:
    def test_user_basic(self):
        u = User(id="@alice:m.org", displayname="Alice", avatar_url="mxc://m.org/av")
        assert bool(u) is True
        assert u.id == "@alice:m.org"
        assert u.displayname == "Alice"
        assert str(u) == "Alice"

    def test_user_no_displayname(self):
        u = User(id="@alice:m.org")
        assert str(u) == "@alice:m.org"

    def test_user_empty(self):
        u = User()
        assert bool(u) is False
        assert str(u) == ""


class TestSenderEnrichment:

    def _sync(self, **kwargs):
        resp = {"next_batch": "s1"}
        resp.update(kwargs)
        return resp

    @pytest.mark.asyncio
    async def test_on_event_has_sender_user(self):
        """Events from rooms with cached members should have sender_user set"""
        client = Client()
        client.restrunner = Mock()
        # Build a room with a member
        r = room([{
            "type": "m.room.member",
            "state_key": "@alice:m.org",
            "content": {"membership": "join", "displayname": "Alice", "avatar_url": "mxc://m.org/av"}
        }], "!r:m.org")
        client.roomCache = {"rooms": {"!r:m.org": r}}
        received = []

        @client.event
        async def on_event(ev):
            received.append(ev)

        sync = self._sync(rooms={"join": {"!r:m.org": {"timeline": {"events": [{
            "type": "m.room.message",
            "sender": "@alice:m.org",
            "content": {"msgtype": "m.text", "body": "hi"},
            "origin_server_ts": 1000,
            "event_id": "$m1"
        }]}}}})

        client.restrunner.sync_async = AsyncMock(return_value=sync)
        client.firstSync = False
        await client._homeserverSync()

        assert len(received) == 1
        assert received[0].sender_user is not None
        assert received[0].sender_user.displayname == "Alice"
        assert received[0].sender_user.avatar_url == "mxc://m.org/av"

    @pytest.mark.asyncio
    async def test_typed_event_has_sender_user(self):
        """Typed events (reaction etc) should also get sender_user"""
        client = Client()
        client.restrunner = Mock()
        r = room([{
            "type": "m.room.member",
            "state_key": "@bob:m.org",
            "content": {"membership": "join", "displayname": "Bob"}
        }], "!r:m.org")
        client.roomCache = {"rooms": {"!r:m.org": r}}
        received = []

        @client.event
        async def on_reaction(ev):
            received.append(ev)

        sync = self._sync(rooms={"join": {"!r:m.org": {"timeline": {"events": [{
            "type": "m.reaction",
            "sender": "@bob:m.org",
            "event_id": "$r1",
            "content": {"m.relates_to": {"rel_type": "m.annotation", "event_id": "$t", "key": "👍"}}
        }]}}}})

        client.restrunner.sync_async = AsyncMock(return_value=sync)
        client.firstSync = False
        await client._homeserverSync()

        assert len(received) == 1
        assert received[0].sender_user is not None
        assert received[0].sender_user.displayname == "Bob"

    @pytest.mark.asyncio
    async def test_sender_user_unknown_sender(self):
        """Unknown sender should get a User with just the id"""
        client = Client()
        client.restrunner = Mock()
        client.roomCache = {"rooms": {"!r:m.org": room([], "!r:m.org")}}
        client.restrunner.getRoomState.return_value = []
        received = []

        @client.event
        async def on_event(ev):
            received.append(ev)

        sync = self._sync(rooms={"join": {"!r:m.org": {"timeline": {"events": [{
            "type": "m.room.message",
            "sender": "@unknown:m.org",
            "content": {"msgtype": "m.text", "body": "hi"},
            "origin_server_ts": 1000,
            "event_id": "$m1"
        }]}}}})

        client.restrunner.sync_async = AsyncMock(return_value=sync)
        client.firstSync = False
        await client._homeserverSync()

        assert len(received) == 1
        assert received[0].sender_user is not None
        assert received[0].sender_user.id == "@unknown:m.org"
        assert received[0].sender_user.displayname is None
