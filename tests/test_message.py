import pytest
from halcyon.message import message, MessageContent, Message
from halcyon.enums import msgType


class TestMessage:
    """Test the main message class"""
    
    def test_message_creation_with_text(self, sample_message_event):
        """Test creating a message from a text event"""
        msg = message(sample_message_event)
        
        assert msg._hasData is True
        assert bool(msg) is True
        assert msg.type == "m.room.message"
        assert msg.sender == "@user:matrix.org"
        assert msg.origin_server_ts == 1632894724739
        assert msg.event.id == "$tBqxdcM:matrix.org"
        
    def test_message_content_text(self, sample_message_event):
        """Test message content for text messages"""
        msg = message(sample_message_event)
        
        assert msg.content is not None
        assert bool(msg.content) is True
        assert msg.content.type == msgType("m.text")
        assert msg.content.body == "Hello world"
        assert msg.content.format == "org.matrix.custom.html"
        assert msg.content.formattedBody == "<p>Hello world</p>"
        assert msg.content.url is None
        assert msg.content.info is None or not bool(msg.content.info)
        
    def test_message_creation_with_image(self, sample_image_event):
        """Test creating a message from an image event"""
        msg = message(sample_image_event)
        
        assert msg._hasData is True
        assert msg.type == "m.room.message"
        assert msg.content.type == msgType("m.image")
        assert msg.content.body == "image.jpg"
        assert msg.content.url == "mxc://matrix.org/abcdef123456"
        
    def test_message_with_file_info(self, sample_image_event):
        """Test file info parsing"""
        msg = message(sample_image_event)
        
        assert msg.content.info is not None
        assert bool(msg.content.info) is True
        assert msg.content.info.size == 2534288
        assert msg.content.info.mimetype == "image/jpeg"
        assert msg.content.info.width == 3024
        assert msg.content.info.height == 4032
        
    def test_message_with_thumbnail(self, sample_image_event):
        """Test thumbnail info parsing"""
        msg = message(sample_image_event)
        
        assert msg.content.info.thumbnail is not None
        assert bool(msg.content.info.thumbnail) is True
        assert msg.content.info.thumbnail.width == 300
        assert msg.content.info.thumbnail.height == 300
        assert msg.content.info.thumbnail.size == 46144
        assert msg.content.info.thumbnail.mimetype == "image/jpeg"
        assert msg.content.info.thumbnail.url == "mxc://matrix.org/thumbnail123"
        
    def test_message_edit_detection(self, sample_edit_event):
        """Test that edits are properly detected"""
        msg = message(sample_edit_event)
        
        assert msg.edit is not None
        assert bool(msg.edit) is True
        assert msg.edit.body == "edited message"
        assert msg.edit.formattedBody == "<p>edited message</p>"
        
    def test_message_relates_to(self, sample_edit_event):
        """Test m.relates_to parsing"""
        msg = message(sample_edit_event)
        
        assert msg.relates is not None
        assert bool(msg.relates) is True
        assert msg.relates.type == "m.replace"
        assert msg.relates.eventID == "$originalEvent:matrix.org"
        
    def test_message_without_content(self):
        """Test message with missing content"""
        minimal_event = {
            "type": "m.room.message",
            "sender": "@user:matrix.org",
            "origin_server_ts": 1632894724739,
            "event_id": "$test:matrix.org",
            "content": {}
        }
        msg = message(minimal_event)
        
        assert msg._hasData is True
        assert msg.content is not None
        assert msg.content.body is None
        assert msg.content.type is None
        
    def test_message_with_room(self):
        """Test message with room object attached"""
        from halcyon.room import room
        
        test_room = room(roomID="!test:matrix.org")
        test_event = {
            "type": "m.room.message",
            "sender": "@user:matrix.org",
            "content": {"msgtype": "m.text", "body": "test"},
            "origin_server_ts": 1632894724739,
            "event_id": "$test:matrix.org"
        }
        
        msg = message(test_event, test_room)
        assert msg.room is not None
        assert msg.room.id == "!test:matrix.org"


class TestMessageContent:
    """Test the MessageContent nested class"""
    
    def test_content_with_empty_data(self):
        """Test MessageContent with None/empty data"""
        from halcyon.message import message
        
        content = message.messageContent(None)
        assert bool(content) is False
        assert content.type is None
        assert content.body is None
        
    def test_content_boolean_check(self):
        """Test __bool__ behavior"""
        from halcyon.message import message
        
        # With data
        content = message.messageContent({"msgtype": "m.text", "body": "test"})
        assert bool(content) is True
        
        # Without data
        empty_content = message.messageContent(None)
        assert bool(empty_content) is False
        
    def test_content_with_various_msgtypes(self):
        """Test different message types"""
        from halcyon.message import message
        
        types_to_test = ["m.text", "m.emote", "m.notice", "m.image", 
                        "m.file", "m.audio", "m.video"]
        
        for msgtype in types_to_test:
            content = message.messageContent({"msgtype": msgtype, "body": "test"})
            assert content.type == msgType(msgtype)
            assert content.body == "test"


class TestFileInfo:
    """Test the FileInfo nested class"""
    
    def test_file_info_basic(self):
        """Test basic file info parsing"""
        from halcyon.message import message
        
        info_data = {
            "size": 1024,
            "mimetype": "image/png",
            "w": 800,
            "h": 600
        }
        
        file_info = message.messageContent.fileInfo(info_data)
        assert bool(file_info) is True
        assert file_info.size == 1024
        assert file_info.mimetype == "image/png"
        assert file_info.width == 800
        assert file_info.height == 600
        
    def test_file_info_with_duration(self):
        """Test file info with duration (for audio/video)"""
        from halcyon.message import message
        
        info_data = {
            "size": 5000000,
            "mimetype": "video/mp4",
            "duration": 120000,
            "w": 1920,
            "h": 1080
        }
        
        file_info = message.messageContent.fileInfo(info_data)
        assert file_info.duration == 120000
        
    def test_file_info_empty(self):
        """Test empty file info"""
        from halcyon.message import message
        
        file_info = message.messageContent.fileInfo(None)
        assert bool(file_info) is False
        assert file_info.size is None


class TestFileThumbnail:
    """Test the FileThumbnail nested class"""
    
    def test_thumbnail_info(self):
        """Test thumbnail info parsing"""
        from halcyon.message import message
        
        thumb_data = {
            "h": 150,
            "w": 150,
            "mimetype": "image/jpeg",
            "size": 10000
        }
        
        thumbnail = message.messageContent.fileInfo.fileThumbnail(
            thumb_data, 
            thumbnailURL="mxc://server/thumb123"
        )
        
        assert bool(thumbnail) is True
        assert thumbnail.width == 150
        assert thumbnail.height == 150
        assert thumbnail.size == 10000
        assert thumbnail.mimetype == "image/jpeg"
        assert thumbnail.url == "mxc://server/thumb123"
        
    def test_thumbnail_with_encrypted_file(self):
        """Test thumbnail with encrypted file reference"""
        from halcyon.message import message
        
        thumb_data = {"h": 100, "w": 100, "size": 5000}
        encrypted_file = {"url": "mxc://encrypted", "key": "somekey"}
        
        thumbnail = message.messageContent.fileInfo.fileThumbnail(
            thumb_data,
            thumbnailFile=encrypted_file
        )
        
        assert thumbnail.file == encrypted_file


class TestIdReturn:
    """Test the idReturn helper class"""
    
    def test_id_return_with_id(self):
        """Test idReturn with valid ID"""
        from halcyon.message import message
        
        id_obj = message.idReturn("$event123:matrix.org")
        assert bool(id_obj) is True
        assert id_obj.id == "$event123:matrix.org"
        
    def test_id_return_without_id(self):
        """Test idReturn with None"""
        from halcyon.message import message
        
        id_obj = message.idReturn(None)
        assert bool(id_obj) is False
        assert id_obj.id is None


class TestRelates:
    """Test the relates nested class"""
    
    def test_relates_replace(self):
        """Test relates_to for edits"""
        from halcyon.message import message
        
        relates_data = {
            "rel_type": "m.replace",
            "event_id": "$original:matrix.org"
        }
        
        relates = message.relates(relates_data)
        assert bool(relates) is True
        assert relates.type == "m.replace"
        assert relates.eventID == "$original:matrix.org"
        
    def test_relates_reply(self):
        """Test relates_to for replies"""
        from halcyon.message import message
        
        relates_data = {
            "m.in_reply_to": {
                "event_id": "$replied:matrix.org"
            }
        }
        
        relates = message.relates(relates_data)
        # Note: Current implementation doesn't handle m.in_reply_to specially
        # This test documents current behavior
        assert relates.type is None  # No rel_type in reply format
        assert relates.eventID is None
        
    def test_relates_empty(self):
        """Test empty relates"""
        from halcyon.message import message
        
        relates = message.relates(None)
        assert bool(relates) is False
        assert relates.type is None
        assert relates.eventID is None


class TestNewMessageTypes:
    """Test new Matrix message types and fields"""
    
    def test_location_message(self):
        """Test location message type"""
        location_content = {
            "msgtype": "m.location",
            "body": "Big Ben, London, UK",
            "geo_uri": "geo:51.5007,-0.1246"
        }
        
        content = MessageContent(location_content)
        assert content.type == msgType.LOCATION
        assert content.body == "Big Ben, London, UK"
        assert content.geo_uri == "geo:51.5007,-0.1246"
    
    def test_server_notice_message(self):
        """Test server notice message type"""
        notice_content = {
            "msgtype": "m.server_notice",
            "body": "Server maintenance scheduled",
            "server_notice_type": "m.server_notice.usage_limit_reached",
            "admin_contact": "mailto:admin@matrix.org",
            "limit_type": "monthly_active_user"
        }
        
        content = MessageContent(notice_content)
        assert content.type == msgType.SERVER_NOTICE
        assert content.body == "Server maintenance scheduled"
        assert content.server_notice_type == "m.server_notice.usage_limit_reached"
        assert content.admin_contact == "mailto:admin@matrix.org"
        assert content.limit_type == "monthly_active_user"
    
    def test_key_verification_request(self):
        """Test key verification request message type"""
        verification_content = {
            "msgtype": "m.key.verification.request",
            "body": "Alice is requesting to verify keys",
            "from_device": "DEVICEID",
            "methods": ["m.sas.v1", "m.qr_code.scan.v1"],
            "to": "@bob:matrix.org"
        }
        
        content = MessageContent(verification_content)
        assert content.type == msgType.KEY_VERIFICATION_REQUEST
        assert content.body == "Alice is requesting to verify keys"
        assert content.from_device == "DEVICEID"
        assert content.methods == ["m.sas.v1", "m.qr_code.scan.v1"]
        assert content.to == "@bob:matrix.org"
    
    def test_file_message_with_filename(self):
        """Test file message with filename field (Matrix v1.10+)"""
        file_content = {
            "msgtype": "m.file",
            "body": "document.pdf",
            "filename": "Important Document.pdf",
            "url": "mxc://matrix.org/file123",
            "info": {
                "size": 123456,
                "mimetype": "application/pdf"
            }
        }
        
        content = MessageContent(file_content)
        assert content.type == msgType.FILE
        assert content.body == "document.pdf"
        assert content.filename == "Important Document.pdf"
        assert content.url == "mxc://matrix.org/file123"
        assert content.info.size == 123456
        assert content.info.mimetype == "application/pdf"
    
    def test_encrypted_file_message(self):
        """Test encrypted file message"""
        encrypted_content = {
            "msgtype": "m.file",
            "body": "encrypted_file.jpg",
            "file": {
                "url": "mxc://matrix.org/encrypted123",
                "key": {"kty": "oct", "k": "base64key"},
                "iv": "base64iv",
                "hashes": {"sha256": "base64hash"},
                "v": "v2"
            },
            "info": {
                "size": 98765,
                "mimetype": "image/jpeg"
            }
        }
        
        content = MessageContent(encrypted_content)
        assert content.type == msgType.FILE
        assert content.body == "encrypted_file.jpg"
        assert content.file is not None
        assert content.file["url"] == "mxc://matrix.org/encrypted123"
        assert content.file["v"] == "v2"
        assert content.url is None  # Should use 'file' instead of 'url' for encrypted
    
    def test_html_formatted_message(self):
        """Test HTML formatted message"""
        formatted_content = {
            "msgtype": "m.text",
            "body": "Hello **world**",
            "format": "org.matrix.custom.html",
            "formatted_body": "Hello <strong>world</strong>"
        }
        
        content = MessageContent(formatted_content)
        assert content.type == msgType.TEXT
        assert content.body == "Hello **world**"
        assert content.format == "org.matrix.custom.html"
        assert content.formattedBody == "Hello <strong>world</strong>"
    
    def test_video_message_with_dimensions(self):
        """Test video message with width/height"""
        video_content = {
            "msgtype": "m.video",
            "body": "video.mp4",
            "url": "mxc://matrix.org/video123",
            "info": {
                "size": 1234567,
                "mimetype": "video/mp4",
                "duration": 120000,
                "w": 1920,
                "h": 1080,
                "thumbnail_url": "mxc://matrix.org/thumb123",
                "thumbnail_info": {
                    "size": 5678,
                    "mimetype": "image/jpeg",
                    "w": 320,
                    "h": 240
                }
            }
        }
        
        content = MessageContent(video_content)
        assert content.type == msgType.VIDEO
        assert content.body == "video.mp4"
        assert content.info.width == 1920
        assert content.info.height == 1080
        assert content.info.duration == 120000
        assert content.info.thumbnail.url == "mxc://matrix.org/thumb123"
        assert content.info.thumbnail.width == 320
        assert content.info.thumbnail.height == 240


class TestBackwardCompatibility:
    """Test that all changes maintain backward compatibility"""
    
    def test_old_style_message_still_works(self):
        """Test that old message format still works"""
        old_message_data = {
            "type": "m.room.message",
            "sender": "@user:matrix.org",
            "content": {
                "msgtype": "m.text",
                "body": "Hello world"
            },
            "origin_server_ts": 1632894724739,
            "event_id": "$test:matrix.org"
        }
        
        msg = Message(old_message_data)
        assert msg.content.body == "Hello world"
        assert msg.content.type == msgType.TEXT
    
    def test_missing_new_fields_graceful_degradation(self):
        """Test that missing new fields don't break existing functionality"""
        basic_content = {
            "msgtype": "m.text",
            "body": "Simple message"
        }
        
        content = MessageContent(basic_content)
        assert content.type == msgType.TEXT
        assert content.body == "Simple message"
        assert content.filename is None
        assert content.geo_uri is None
        assert content.server_notice_type is None
        assert content.from_device is None
        assert content.methods is None