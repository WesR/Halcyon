import pytest
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Shared fixtures for all tests
@pytest.fixture
def sample_message_event():
    """Sample Matrix message event"""
    return {
        "type": "m.room.message",
        "sender": "@user:matrix.org",
        "content": {
            "msgtype": "m.text",
            "body": "Hello world",
            "format": "org.matrix.custom.html",
            "formatted_body": "<p>Hello world</p>"
        },
        "origin_server_ts": 1632894724739,
        "unsigned": {
            "age": 75364
        },
        "event_id": "$tBqxdcM:matrix.org"
    }

@pytest.fixture
def sample_image_event():
    """Sample Matrix image message event"""
    return {
        "type": "m.room.message",
        "sender": "@user:matrix.org",
        "content": {
            "msgtype": "m.image",
            "body": "image.jpg",
            "url": "mxc://matrix.org/abcdef123456",
            "info": {
                "size": 2534288,
                "mimetype": "image/jpeg",
                "w": 3024,
                "h": 4032,
                "thumbnail_info": {
                    "h": 300,
                    "mimetype": "image/jpeg",
                    "size": 46144,
                    "w": 300
                },
                "thumbnail_url": "mxc://matrix.org/thumbnail123"
            }
        },
        "origin_server_ts": 1632894724739,
        "event_id": "$imageEvent:matrix.org"
    }

@pytest.fixture
def sample_edit_event():
    """Sample Matrix edit message event"""
    return {
        "type": "m.room.message",
        "sender": "@user:matrix.org",
        "content": {
            "msgtype": "m.text",
            "body": "* edited message",
            "m.new_content": {
                "msgtype": "m.text",
                "body": "edited message",
                "format": "org.matrix.custom.html",
                "formatted_body": "<p>edited message</p>"
            },
            "m.relates_to": {
                "rel_type": "m.replace",
                "event_id": "$originalEvent:matrix.org"
            }
        },
        "origin_server_ts": 1632894724739,
        "event_id": "$editEvent:matrix.org"
    }

@pytest.fixture
def sample_room_create_events():
    """Sample room state events"""
    return [
        {
            "type": "m.room.create",
            "content": {
                "creator": "@creator:matrix.org",
                "room_version": "6",
                "m.federate": True,
                "predecessor": {
                    "event_id": "$something:example.org",
                    "room_id": "!oldroom:example.org"
                }
            }
        },
        {
            "type": "m.room.name",
            "content": {
                "name": "Test Room"
            }
        },
        {
            "type": "m.room.topic",
            "content": {
                "topic": "A test room for unit tests"
            }
        },
        {
            "type": "m.room.join_rules",
            "content": {
                "join_rule": "invite"
            }
        },
        {
            "type": "m.room.power_levels",
            "content": {
                "users": {
                    "@creator:matrix.org": 100,
                    "@moderator:matrix.org": 50
                },
                "users_default": 0,
                "events_default": 0,
                "state_default": 50,
                "invite": 50,
                "redact": 50,
                "ban": 50,
                "kick": 50,
                "events": {
                    "m.room.name": 50,
                    "m.room.topic": 50
                }
            }
        },
        {
            "type": "m.room.member",
            "content": {
                "membership": "join"
            },
            "user_id": "@user1:matrix.org",
            "state_key": "@user1:matrix.org"
        },
        {
            "type": "m.room.member",
            "content": {
                "membership": "invite"
            },
            "state_key": "@invited:matrix.org"
        },
        {
            "type": "m.room.encryption",
            "content": {
                "algorithm": "m.megolm.v1.aes-sha2",
                "rotation_period_ms": 604800000,
                "rotation_period_msgs": 100
            }
        }
    ]

@pytest.fixture
def sample_room_with_acl():
    """Room events including ACL"""
    return [
        {
            "type": "m.room.create",
            "content": {
                "creator": "@admin:matrix.org"
            }
        },
        {
            "type": "m.room.server_acl",
            "content": {
                "allow_ip_literals": False,
                "allow": ["matrix.org", "*.matrix.org"],
                "deny": ["bad.server.com"]
            }
        }
    ]