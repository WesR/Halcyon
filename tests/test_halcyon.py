import pytest
import json
import base64
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from halcyon.halcyon import Client
from halcyon.message import message
from halcyon.room import room


class TestClient:
    """Test the main Client class"""
    
    def test_client_initialization(self):
        """Test basic client initialization"""
        client = Client()

        assert client.loop is None  # No running loop at init time
        assert client.logoutOnDeath is False
        assert client.loopPollInterval == 0.1
        assert client.long_poll_timeout == 10
        assert client.restrunner is None
        assert client.sinceToken == ""
        assert client.encryptedCurveCount == 0
        assert client.ignoreFirstSync is True
        assert client.firstSync is True
        assert isinstance(client.roomCache, dict)
        
    def test_client_initialization_with_params(self):
        """Test client initialization with custom parameters"""
        import asyncio
        loop = asyncio.new_event_loop()
        
        client = Client(loop=loop, ignoreFirstSync=False)
        
        assert client.loop is loop
        assert client.ignoreFirstSync is False
        
        loop.close()


class TestTokenHandling:
    """Test token encoding/decoding functionality"""
    
    def test_encode_token_dict(self):
        """Test token dictionary encoding"""
        client = Client()
        
        test_dict = {"typ": "engine", "hsvr": "matrix.org", "user": "@test:matrix.org"}
        encoded = client._encodeTokenDict(test_dict)
        
        # Should be valid base64
        assert isinstance(encoded, str)
        decoded_bytes = base64.b64decode(encoded)
        decoded_str = str(decoded_bytes, "utf-8")
        parsed = json.loads(decoded_str)
        
        assert parsed == test_dict
        
    def test_decode_token_dict(self):
        """Test token dictionary decoding"""
        client = Client()
        
        test_dict = {"typ": "valid-token", "token": "abc123", "device_id": "DEVICE"}
        encoded = base64.b64encode(bytes(json.dumps(test_dict), "utf-8"))
        encoded_str = str(encoded, "utf-8")
        
        decoded = client._decodeTokenDict(encoded_str)
        assert decoded == test_dict
        
    def test_decode_invalid_token(self):
        """Test decoding invalid token"""
        client = Client()
        
        with patch('builtins.exit') as mock_exit:
            with patch('logging.error') as mock_log:
                client._decodeTokenDict("invalid_base64!")
                mock_log.assert_called()
                mock_exit.assert_called()


class TestRoomCache:
    """Test room caching functionality"""
    
    def test_room_cache_initialization(self):
        """Test room cache setup"""
        client = Client()
        
        # Mock restrunner
        client.restrunner = Mock()
        client.restrunner.joinedRooms.return_value = ["!room1:matrix.org", "!room2:matrix.org"]
        client.restrunner.getRoomState.return_value = []
        
        client._roomcacheinit()
        
        assert "cache_age" in client.roomCache
        assert "rooms" in client.roomCache
        assert isinstance(client.roomCache["rooms"], dict)
        
        # Should have called getRoomState for each room
        assert client.restrunner.getRoomState.call_count == 2
        
    def test_add_room_to_cache(self):
        """Test adding a room to cache"""
        client = Client()
        client.roomCache = {"rooms": {}}
        
        # Mock restrunner
        client.restrunner = Mock()
        client.restrunner.getRoomState.return_value = [
            {
                "type": "m.room.create",
                "content": {"creator": "@user:matrix.org"}
            }
        ]
        
        client._addRoomToCache("!test:matrix.org")
        
        assert "!test:matrix.org" in client.roomCache["rooms"]
        assert isinstance(client.roomCache["rooms"]["!test:matrix.org"], room)
        
    def test_get_room_cached(self):
        """Test getting room from cache"""
        client = Client()
        test_room = room(roomID="!test:matrix.org")
        client.roomCache = {
            "rooms": {"!test:matrix.org": test_room}
        }
        
        retrieved_room = client._getRoom("!test:matrix.org")
        assert retrieved_room is test_room
        
    def test_get_room_not_cached(self):
        """Test getting room not in cache"""
        client = Client()
        client.roomCache = {"rooms": {}}
        
        # Mock restrunner
        client.restrunner = Mock()
        client.restrunner.getRoomState.return_value = [
            {
                "type": "m.room.create",
                "content": {"creator": "@user:matrix.org"}
            }
        ]
        
        retrieved_room = client._getRoom("!test:matrix.org")
        
        # Should have been added to cache
        assert "!test:matrix.org" in client.roomCache["rooms"]
        assert isinstance(retrieved_room, room)
        
    def test_get_room_fails_to_populate(self):
        """Test getting room that fails to populate"""
        client = Client()
        client.roomCache = {"rooms": {}}
        
        # Mock restrunner that fails to get state
        client.restrunner = Mock()
        client.restrunner.getRoomState.return_value = None
        
        with patch.object(client, '_addRoomToCache') as mock_add:
            # Make _addRoomToCache not actually add anything
            mock_add.return_value = None
            
            retrieved_room = client._getRoom("!test:matrix.org")
            
            # Should return empty room
            assert isinstance(retrieved_room, room)
            assert retrieved_room.id is None


class TestEventStubs:
    """Test event handler stubs"""
    
    @pytest.mark.asyncio
    async def test_on_ready_stub(self):
        """Test on_ready stub does nothing"""
        client = Client()
        result = await client.on_ready()
        assert result is None
        
    @pytest.mark.asyncio
    async def test_on_message_stub(self):
        """Test on_message stub does nothing"""
        client = Client()
        mock_message = Mock()
        result = await client.on_message(mock_message)
        assert result is None
        
    @pytest.mark.asyncio
    async def test_on_message_edit_stub(self):
        """Test on_message_edit stub does nothing"""
        client = Client()
        mock_message = Mock()
        result = await client.on_message_edit(mock_message)
        assert result is None
        
    @pytest.mark.asyncio
    async def test_on_room_invite_stub(self):
        """Test on_room_invite stub does nothing"""
        client = Client()
        mock_room = Mock()
        result = await client.on_room_invite(mock_room)
        assert result is None
        
    @pytest.mark.asyncio
    async def test_on_room_leave_stub(self):
        """Test on_room_leave stub does nothing"""
        client = Client()
        result = await client.on_room_leave("!test:matrix.org")
        assert result is None


class TestEventDecorator:
    """Test the @client.event decorator"""
    
    def test_event_decorator(self):
        """Test that event decorator properly sets handler"""
        client = Client()
        
        @client.event
        async def on_message(message):
            return "custom handler called"
            
        # Should have replaced the stub
        assert hasattr(client, 'on_message')
        assert client.on_message.__name__ == 'on_message'


class TestMessageSending:
    """Test message sending functionality"""
    
    @pytest.mark.asyncio
    async def test_send_message_basic(self):
        """Test basic message sending"""
        client = Client()
        client.restrunner = Mock()
        client.restrunner.sendEvent_async = AsyncMock(return_value={"event_id": "$sent:matrix.org"})

        result = await client.send_message("!room:matrix.org", "Hello world")

        client.restrunner.sendEvent_async.assert_called_once()
        call_args = client.restrunner.sendEvent_async.call_args

        assert call_args[1]["roomID"] == "!room:matrix.org"
        assert call_args[1]["eventType"] == "m.room.message"
        assert call_args[1]["eventPayload"]["msgtype"] == "m.text"
        assert call_args[1]["eventPayload"]["body"] == "Hello world"

    @pytest.mark.asyncio
    async def test_send_message_notice(self):
        """Test sending notice message"""
        client = Client()
        client.restrunner = Mock()
        client.restrunner.sendEvent_async = AsyncMock(return_value={"event_id": "$sent:matrix.org"})

        await client.send_message("!room:matrix.org", "Notice", isNotice=True)

        call_args = client.restrunner.sendEvent_async.call_args
        assert call_args[1]["eventPayload"]["msgtype"] == "m.notice"

    @pytest.mark.asyncio
    async def test_send_message_markdown(self):
        """Test sending markdown message"""
        client = Client()
        client.restrunner = Mock()
        client.restrunner.sendEvent_async = AsyncMock(return_value={"event_id": "$sent:matrix.org"})

        await client.send_message("!room:matrix.org", "**Bold text**", textFormat="markdown")

        call_args = client.restrunner.sendEvent_async.call_args
        payload = call_args[1]["eventPayload"]

        assert payload["format"] == "org.matrix.custom.html"
        assert "formatted_body" in payload
        assert "<strong>" in payload["formatted_body"]

    @pytest.mark.asyncio
    async def test_send_message_html(self):
        """Test sending HTML message"""
        client = Client()
        client.restrunner = Mock()
        client.restrunner.sendEvent_async = AsyncMock(return_value={"event_id": "$sent:matrix.org"})

        html_content = "<p><strong>Bold text</strong></p>"
        await client.send_message("!room:matrix.org", html_content, textFormat="html")

        call_args = client.restrunner.sendEvent_async.call_args
        payload = call_args[1]["eventPayload"]

        assert payload["format"] == "org.matrix.custom.html"
        assert payload["formatted_body"] == html_content
        assert "<" not in payload["body"]

    @pytest.mark.asyncio
    async def test_send_message_reply(self):
        """Test sending reply message"""
        client = Client()
        client.restrunner = Mock()
        client.restrunner.sendEvent_async = AsyncMock(return_value={"event_id": "$sent:matrix.org"})

        await client.send_message("!room:matrix.org", "Reply text", replyTo="$original:matrix.org")

        call_args = client.restrunner.sendEvent_async.call_args
        payload = call_args[1]["eventPayload"]

        assert "m.relates_to" in payload
        assert payload["m.relates_to"]["m.in_reply_to"]["event_id"] == "$original:matrix.org"


class TestTyping:
    """Test typing indicator functionality"""
    
    @pytest.mark.asyncio
    async def test_send_typing(self):
        """Test sending typing indicator"""
        client = Client()
        client.restrunner = Mock()
        
        await client.send_typing("!room:matrix.org", 30)
        
        client.restrunner.sendTyping.assert_called_once_with("!room:matrix.org", 30)
        
    @pytest.mark.asyncio
    async def test_send_typing_default(self):
        """Test sending typing with default duration"""
        client = Client()
        client.restrunner = Mock()
        
        await client.send_typing("!room:matrix.org")
        
        client.restrunner.sendTyping.assert_called_once_with("!room:matrix.org", None)


class TestRoomOperations:
    """Test room-related operations"""
    
    @pytest.mark.asyncio
    async def test_join_room(self):
        """Test joining a room"""
        client = Client()
        client.restrunner = Mock()
        client.restrunner.joinRoom.return_value = {"room_id": "!room:matrix.org"}
        client.roomCache = {"rooms": {}}
        
        with patch.object(client, '_addRoomToCache') as mock_add:
            result = await client.join_room("!room:matrix.org")
            
            client.restrunner.joinRoom.assert_called_once_with("!room:matrix.org")
            mock_add.assert_called_once_with("!room:matrix.org")


class TestPresence:
    """Test presence functionality"""
    
    @pytest.mark.asyncio
    async def test_change_presence(self):
        """Test changing presence"""
        client = Client()
        client.restrunner = Mock()
        client.restrunner.setUserPresence.return_value = {}
        
        await client.change_presence(presence="online", statusMessage="Working on code")
        
        client.restrunner.setUserPresence.assert_called_once_with(
            presence="online", 
            statusMessage="Working on code"
        )
        
    @pytest.mark.asyncio
    async def test_change_presence_error(self):
        """Test presence change with error"""
        client = Client()
        client.restrunner = Mock()
        client.restrunner.setUserPresence.return_value = {
            "errcode": "M_FORBIDDEN",
            "error": "Not allowed"
        }
        
        with patch('logging.error') as mock_log:
            await client.change_presence(presence="away")
            mock_log.assert_called_with("Change presence error: Not allowed")


class TestMediaOperations:
    """Test media upload/download functionality"""
    
    @pytest.mark.asyncio
    async def test_download_media(self):
        """Test downloading media"""
        client = Client()
        client.restrunner = Mock()
        client.restrunner.getMediaFromMXC_async = AsyncMock(return_value=b"fake_image_data")

        result = await client.download_media("mxc://matrix.org/abc123")

        client.restrunner.getMediaFromMXC_async.assert_called_once_with("mxc://matrix.org/abc123")
        assert result == b"fake_image_data"

    @pytest.mark.asyncio
    async def test_upload_media(self):
        """Test uploading media"""
        client = Client()
        client.restrunner = Mock()
        client.restrunner.uploadMedia_async = AsyncMock(return_value={"content_uri": "mxc://matrix.org/uploaded123"})

        import io
        fake_buffer = io.BytesIO(b"fake_file_data")

        result = await client.upload_media(fake_buffer, "test.txt")

        client.restrunner.uploadMedia_async.assert_called_once_with(
            fileData=fake_buffer,
            fileName="test.txt"
        )
        assert result["content_uri"] == "mxc://matrix.org/uploaded123"


class TestFileSending:
    """Test file sending functionality"""
    
    @pytest.mark.asyncio
    async def test_send_file_basic(self):
        """Test basic file sending"""
        client = Client()
        client.restrunner = Mock()
        client.restrunner.sendEvent_async = AsyncMock(return_value={"event_id": "$file:matrix.org"})

        result = await client._send_file(
            roomID="!room:matrix.org",
            body="test.txt",
            fileURL="mxc://matrix.org/file123"
        )

        call_args = client.restrunner.sendEvent_async.call_args
        payload = call_args[1]["eventPayload"]

        assert payload["msgtype"] == "m.file"
        assert payload["body"] == "test.txt"
        assert payload["url"] == "mxc://matrix.org/file123"

    @pytest.mark.asyncio
    async def test_send_file_with_info(self):
        """Test file sending with info"""
        from halcyon.enums import msgType

        client = Client()
        client.restrunner = Mock()
        client.restrunner.sendEvent_async = AsyncMock(return_value={"event_id": "$file:matrix.org"})

        file_info = {
            "size": 1024,
            "mimetype": "text/plain"
        }

        await client._send_file(
            roomID="!room:matrix.org",
            body="test.txt",
            fileURL="mxc://matrix.org/file123",
            messageType=msgType.IMAGE,
            info=file_info,
            fileName="actual_file.txt"
        )

        call_args = client.restrunner.sendEvent_async.call_args
        payload = call_args[1]["eventPayload"]

        assert payload["msgtype"] == msgType.IMAGE
        assert payload["info"] == file_info
        assert payload["filename"] == "actual_file.txt"


class TestSyncPipeline:
    """Test the sync event pipeline dispatches correctly"""

    def _make_sync_response(self, **kwargs):
        """Build a minimal /sync response"""
        resp = {"next_batch": "s1234"}
        resp.update(kwargs)
        return resp

    @pytest.mark.asyncio
    async def test_sync_skips_first_sync(self):
        """First sync should be skipped when ignoreFirstSync is True"""
        client = Client()
        client.restrunner = Mock()
        client.restrunner.sync_async = AsyncMock(return_value=self._make_sync_response())
        client.ignoreFirstSync = True
        client.firstSync = True

        await client._homeserverSync()

        assert client.firstSync is False
        assert client.sinceToken == "s1234"

    @pytest.mark.asyncio
    async def test_sync_dispatches_message(self):
        """Timeline m.room.message events dispatch to on_message"""
        client = Client()
        client.restrunner = Mock()
        client.roomCache = {"rooms": {}}
        client.restrunner.getRoomState.return_value = []
        received = []

        @client.event
        async def on_message(msg):
            received.append(msg)

        sync_resp = self._make_sync_response(rooms={
            "join": {
                "!room:matrix.org": {
                    "timeline": {
                        "events": [{
                            "type": "m.room.message",
                            "sender": "@alice:matrix.org",
                            "content": {"msgtype": "m.text", "body": "hello"},
                            "origin_server_ts": 1000,
                            "event_id": "$msg1"
                        }]
                    }
                }
            }
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
        assert len(received) == 1
        assert received[0].content.body == "hello"

    @pytest.mark.asyncio
    async def test_sync_dispatches_edit(self):
        """Timeline edit events dispatch to on_message_edit"""
        client = Client()
        client.restrunner = Mock()
        client.roomCache = {"rooms": {}}
        client.restrunner.getRoomState.return_value = []
        received = []

        @client.event
        async def on_message_edit(msg):
            received.append(msg)

        sync_resp = self._make_sync_response(rooms={
            "join": {
                "!room:matrix.org": {
                    "timeline": {
                        "events": [{
                            "type": "m.room.message",
                            "sender": "@alice:matrix.org",
                            "content": {
                                "msgtype": "m.text",
                                "body": "* edited",
                                "m.new_content": {"msgtype": "m.text", "body": "edited"},
                                "m.relates_to": {"rel_type": "m.replace", "event_id": "$orig"}
                            },
                            "origin_server_ts": 1000,
                            "event_id": "$edit1"
                        }]
                    }
                }
            }
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
        assert len(received) == 1
        assert received[0].edit.body == "edited"

    @pytest.mark.asyncio
    async def test_sync_dispatches_invite(self):
        """Invite rooms dispatch to on_room_invite"""
        client = Client()
        client.restrunner = Mock()
        received = []

        @client.event
        async def on_room_invite(rm):
            received.append(rm)

        sync_resp = self._make_sync_response(rooms={
            "invite": {
                "!invited:matrix.org": {
                    "invite_state": {
                        "events": [{
                            "type": "m.room.name",
                            "content": {"name": "Invite Room"}
                        }]
                    }
                }
            }
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
        assert len(received) == 1
        assert received[0].name == "Invite Room"

    @pytest.mark.asyncio
    async def test_invite_events_also_fire_on_event(self):
        client = Client()
        client.restrunner = Mock()
        received = []

        @client.event
        async def on_event(ev):
            received.append(ev)

        sync_resp = self._make_sync_response(rooms={
            "invite": {
                "!invited:matrix.org": {
                    "invite_state": {
                        "events": [{
                            "type": "m.room.name",
                            "content": {"name": "Invite Room"}
                        }]
                    }
                }
            }
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
        assert len(received) == 1
        assert received[0].source == "invite_state"
        assert received[0].room_id == "!invited:matrix.org"

    @pytest.mark.asyncio
    async def test_knock_events_fire_on_event(self):
        client = Client()
        client.restrunner = Mock()
        received = []

        @client.event
        async def on_event(ev):
            received.append(ev)

        sync_resp = self._make_sync_response(rooms={
            "knock": {
                "!knocked:matrix.org": {
                    "knock_state": {
                        "events": [{
                            "type": "m.room.name",
                            "content": {"name": "Knock Room"}
                        }]
                    }
                }
            }
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
        assert len(received) == 1
        assert received[0].source == "knock_state"
        assert received[0].room_id == "!knocked:matrix.org"

    @pytest.mark.asyncio
    async def test_sync_dispatches_leave(self):
        """Leave rooms dispatch to on_room_leave"""
        client = Client()
        client.restrunner = Mock()
        received = []

        @client.event
        async def on_room_leave(room_id):
            received.append(room_id)

        sync_resp = self._make_sync_response(rooms={
            "leave": {"!left:matrix.org": {}}
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
        assert received == ["!left:matrix.org"]

    @pytest.mark.asyncio
    async def test_leave_events_also_fire_on_event(self):
        client = Client()
        client.restrunner = Mock()
        received = []

        @client.event
        async def on_event(ev):
            received.append(ev)

        sync_resp = self._make_sync_response(rooms={
            "leave": {
                "!left:matrix.org": {
                    "timeline": {
                        "events": [{
                            "type": "m.room.member",
                            "state_key": "@user:matrix.org",
                            "content": {"membership": "leave"}
                        }]
                    }
                }
            }
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
        assert len(received) == 1
        assert received[0].source == "leave_timeline"
        assert received[0].room_id == "!left:matrix.org"

    @pytest.mark.asyncio
    async def test_sync_dispatches_sticker_to_on_message(self):
        client = Client()
        client.restrunner = Mock()
        client.roomCache = {"rooms": {}}
        client.restrunner.getRoomState.return_value = []
        received = []

        @client.event
        async def on_message(msg):
            received.append(msg)

        sync_resp = self._make_sync_response(rooms={
            "join": {
                "!room:matrix.org": {
                    "timeline": {
                        "events": [{
                            "type": "m.sticker",
                            "sender": "@alice:matrix.org",
                            "content": {
                                "body": "party parrot",
                                "url": "mxc://matrix.org/sticker123",
                                "info": {"mimetype": "image/png", "w": 128, "h": 128}
                            },
                            "origin_server_ts": 1000,
                            "event_id": "$sticker1"
                        }]
                    }
                }
            }
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
        assert len(received) == 1
        assert received[0].is_sticker is True
        assert received[0].content.body == "party parrot"

    def test_get_bot_info_includes_auth_type(self):
        client = Client()
        client.restrunner = Mock()
        client.restrunner.USER_ID = "@bot:matrix.org"
        client.restrunner.DEVICE_ID = "DEVICE"
        client.restrunner.HOMESERVER = "https://matrix.org"
        client.auth_type = "token"

        info = client.get_bot_info()
        assert info["auth_type"] == "token"
        assert info["user_id"] == "@bot:matrix.org"

    @pytest.mark.asyncio
    async def test_sync_handles_bad_response(self):
        """Sync with missing next_batch returns early"""
        client = Client()
        client.restrunner = Mock()
        client.restrunner.sync_async = AsyncMock(return_value={})

        await client._homeserverSync()
        assert client.sinceToken == ""

    @pytest.mark.asyncio
    async def test_sync_processes_all_joined_room_streams(self):
        """All joined room streams are iterated without error"""
        client = Client()
        client.restrunner = Mock()
        client.roomCache = {"rooms": {}}
        client.restrunner.getRoomState.return_value = []

        sync_resp = self._make_sync_response(rooms={
            "join": {
                "!room:matrix.org": {
                    "state": {"events": [{"type": "m.room.name", "content": {"name": "X"}}]},
                    "timeline": {"events": []},
                    "ephemeral": {"events": [{"type": "m.typing", "content": {}}]},
                    "account_data": {"events": [{"type": "m.tag", "content": {}}]},
                }
            }
        })

        client.restrunner.sync_async = AsyncMock(return_value=sync_resp)
        client.firstSync = False

        await client._homeserverSync()
