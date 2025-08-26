import pytest
from halcyon.room import room


class TestRoom:
    """Test the main room class"""
    
    def test_room_creation_empty(self):
        """Test creating an empty room"""
        test_room = room()
        assert bool(test_room) is False
        assert test_room._hasData is False
        assert test_room.id is None
        
    def test_room_creation_with_id(self):
        """Test creating room with just ID"""
        test_room = room(roomID="!test:matrix.org")
        assert test_room.id == "!test:matrix.org"
        assert bool(test_room) is False  # No events processed yet
        
    def test_room_creation_with_events(self, sample_room_create_events):
        """Test room creation with full event list"""
        test_room = room(sample_room_create_events, "!test:matrix.org")
        
        assert bool(test_room) is True
        assert test_room.id == "!test:matrix.org"
        assert test_room.creator == "@creator:matrix.org"
        assert test_room.version == "6"
        assert test_room.federated is True
        assert test_room.name == "Test Room"
        assert test_room.topic == "A test room for unit tests"
        assert test_room.joinRule == "invite"
        
    def test_room_predecessor(self, sample_room_create_events):
        """Test room predecessor parsing"""
        test_room = room(sample_room_create_events, "!test:matrix.org")
        
        assert test_room.predecessor is not None
        assert bool(test_room.predecessor) is True
        assert test_room.predecessor.room.id == "!oldroom:example.org"
        assert test_room.predecessor.event.id == "$something:example.org"
        
    def test_room_members(self, sample_room_create_events):
        """Test member list parsing"""
        test_room = room(sample_room_create_events, "!test:matrix.org")
        
        # Should have one joined member
        assert len(test_room.members) == 1
        assert "@user1:matrix.org" in test_room.members
        
        # Should have one invited member
        assert len(test_room.invited) == 1
        assert "@invited:matrix.org" in test_room.invited
        
        # No left members in our sample
        assert len(test_room.left) == 0
        
    def test_room_permissions(self, sample_room_create_events):
        """Test power levels parsing"""
        test_room = room(sample_room_create_events, "!test:matrix.org")
        
        assert test_room.permissions is not None
        assert bool(test_room.permissions) is True
        
        # Check admin/mod detection
        assert "@creator:matrix.org" in test_room.permissions.administrators
        assert "@moderator:matrix.org" in test_room.permissions.moderators
        
        # Check defaults
        assert test_room.permissions.user_value == 0
        assert test_room.permissions.events_value == 0
        assert test_room.permissions.state_value == 50
        
        # Check action levels
        assert test_room.permissions.invite_value == 50
        assert test_room.permissions.redact_value == 50
        
    def test_room_encryption(self, sample_room_create_events):
        """Test encryption settings parsing"""
        test_room = room(sample_room_create_events, "!test:matrix.org")
        
        assert test_room.encryption is not None
        assert bool(test_room.encryption) is True
        assert test_room.encryption.algorithm == "m.megolm.v1.aes-sha2"
        assert test_room.encryption.rotation_period_ms == 604800000
        assert test_room.encryption.rotation_period_msgs == 100
        
    def test_room_server_acl(self, sample_room_with_acl):
        """Test server ACL parsing"""
        test_room = room(sample_room_with_acl, "!acl:matrix.org")
        
        assert test_room.acl is not None
        assert bool(test_room.acl) is True
        assert test_room.acl.allow_ip_literals is False
        assert "matrix.org" in test_room.acl.allow
        assert "*.matrix.org" in test_room.acl.allow
        assert "bad.server.com" in test_room.acl.deny


class TestRoomPredecessor:
    """Test the roomPredecessor nested class"""
    
    def test_predecessor_with_data(self):
        """Test predecessor with valid data"""
        predecessor_data = {
            "event_id": "$event:server.org",
            "room_id": "!room:server.org"
        }
        
        predecessor = room.roomPredecessor(predecessor_data)
        assert bool(predecessor) is True
        assert predecessor.event.id == "$event:server.org"
        assert predecessor.room.id == "!room:server.org"
        
    def test_predecessor_empty(self):
        """Test predecessor with no data"""
        predecessor = room.roomPredecessor(None)
        assert bool(predecessor) is False
        assert predecessor.event is None
        assert predecessor.room is None
        
    def test_predecessor_partial_data(self):
        """Test predecessor with missing fields"""
        predecessor_data = {"event_id": "$event:server.org"}
        
        predecessor = room.roomPredecessor(predecessor_data)
        assert bool(predecessor) is True
        assert predecessor.event.id == "$event:server.org"
        assert predecessor.room.id is None


class TestRoomPermissions:
    """Test the roomPermissions nested class"""
    
    def test_permissions_basic(self):
        """Test basic permission parsing"""
        perms_data = {
            "users": {
                "@admin:matrix.org": 100,
                "@mod:matrix.org": 50,
                "@user:matrix.org": 0
            },
            "users_default": 0,
            "events_default": 0,
            "state_default": 50,
            "invite": 50,
            "redact": 50,
            "ban": 50,
            "kick": 50
        }
        
        perms = room.roomPermissions(perms_data)
        assert bool(perms) is True
        
        # Check synthetic fields
        assert len(perms.administrators) == 1
        assert "@admin:matrix.org" in perms.administrators
        assert len(perms.moderators) == 1
        assert "@mod:matrix.org" in perms.moderators
        
        # Check all users
        assert len(perms.users) == 3
        assert perms.users["@user:matrix.org"] == 0
        
    def test_permissions_with_events(self):
        """Test permissions with event-specific power levels"""
        perms_data = {
            "users": {"@admin:matrix.org": 100},
            "events": {
                "m.room.name": 50,
                "m.room.topic": 75,
                "m.room.power_levels": 100
            }
        }
        
        perms = room.roomPermissions(perms_data)
        assert perms.m_event_values is not None
        assert perms.m_event_values["m.room.name"] == 50
        assert perms.m_event_values["m.room.topic"] == 75
        
    def test_permissions_empty(self):
        """Test empty permissions"""
        perms = room.roomPermissions(None)
        assert bool(perms) is False


class TestRoomServerAcl:
    """Test the room_server_acl nested class"""
    
    def test_acl_full(self):
        """Test full ACL configuration"""
        acl_data = {
            "allow_ip_literals": False,
            "allow": ["good.server.com", "*.trusted.org"],
            "deny": ["bad.server.com", "*.evil.org"]
        }
        
        acl = room.room_server_acl(acl_data)
        assert bool(acl) is True
        assert acl.allow_ip_literals is False
        assert len(acl.allow) == 2
        assert "good.server.com" in acl.allow
        assert len(acl.deny) == 2
        assert "bad.server.com" in acl.deny
        
    def test_acl_minimal(self):
        """Test ACL with minimal data"""
        acl_data = {"allow_ip_literals": True}
        
        acl = room.room_server_acl(acl_data)
        assert bool(acl) is True
        assert acl.allow_ip_literals is True
        assert acl.allow == []  # Default empty list
        assert acl.deny == []   # Default empty list
        
    def test_acl_empty(self):
        """Test empty ACL"""
        acl = room.room_server_acl(None)
        assert bool(acl) is False


class TestRoomEncryption:
    """Test the room_encryption nested class"""
    
    def test_encryption_full(self):
        """Test full encryption configuration"""
        encryption_data = {
            "algorithm": "m.megolm.v1.aes-sha2",
            "rotation_period_ms": 604800000,
            "rotation_period_msgs": 100
        }
        
        encryption = room.room_encryption(encryption_data)
        assert bool(encryption) is True
        assert encryption.algorithm == "m.megolm.v1.aes-sha2"
        assert encryption.rotation_period_ms == 604800000
        assert encryption.rotation_period_msgs == 100
        
    def test_encryption_minimal(self):
        """Test encryption with just algorithm"""
        encryption_data = {"algorithm": "m.megolm.v1.aes-sha2"}
        
        encryption = room.room_encryption(encryption_data)
        assert bool(encryption) is True
        assert encryption.algorithm == "m.megolm.v1.aes-sha2"
        assert encryption.rotation_period_ms is None
        assert encryption.rotation_period_msgs is None
        
    def test_encryption_empty(self):
        """Test empty encryption"""
        encryption = room.room_encryption(None)
        assert bool(encryption) is False


class TestRoomAvatar:
    """Test the room_avatar nested class"""
    
    def test_avatar_with_url(self):
        """Test avatar with MXC URL"""
        avatar_data = {"url": "mxc://matrix.org/avatar123"}
        
        avatar = room.room_avatar(avatar_data)
        assert bool(avatar) is True
        assert avatar.url == "mxc://matrix.org/avatar123"
        
    def test_avatar_empty(self):
        """Test empty avatar"""
        avatar = room.room_avatar(None)
        assert bool(avatar) is False
        assert avatar.url is None


class TestRoomAlias:
    """Test the room_alias nested class"""
    
    def test_alias_with_canonical_and_alt(self):
        """Test alias with canonical and alternatives"""
        alias_data = {
            "alias": "#main:matrix.org",
            "alt_aliases": ["#alt1:matrix.org", "#alt2:matrix.org"]
        }
        
        alias = room.room_alias(alias_data)
        assert bool(alias) is True
        assert alias.canonical == "#main:matrix.org"
        assert len(alias.alt) == 2
        assert "#alt1:matrix.org" in alias.alt
        assert "#alt2:matrix.org" in alias.alt
        
    def test_alias_canonical_only(self):
        """Test alias with only canonical"""
        alias_data = {"alias": "#room:matrix.org"}
        
        alias = room.room_alias(alias_data)
        assert bool(alias) is True
        assert alias.canonical == "#room:matrix.org"
        assert len(alias.alt) == 0
        
    def test_alias_alt_only(self):
        """Test alias with only alternatives"""
        alias_data = {"alt_aliases": ["#alt:matrix.org"]}
        
        alias = room.room_alias(alias_data)
        assert bool(alias) is True
        assert alias.canonical is None
        assert len(alias.alt) == 1
        assert "#alt:matrix.org" in alias.alt
        
    def test_alias_empty(self):
        """Test empty alias"""
        alias = room.room_alias(None)
        assert bool(alias) is False
        assert alias.canonical is None
        assert len(alias.alt) == 0


class TestRoomDefaults:
    """Test default values according to Matrix spec"""
    
    def test_room_version_default(self):
        """Test room version defaults to 1"""
        events = [{
            "type": "m.room.create",
            "content": {"creator": "@user:matrix.org"}  # No room_version
        }]
        
        test_room = room(events, "!test:matrix.org")
        assert test_room.version == 1  # Default per spec
        
    def test_federate_default(self):
        """Test m.federate defaults to True"""
        events = [{
            "type": "m.room.create",
            "content": {"creator": "@user:matrix.org"}  # No m.federate
        }]
        
        test_room = room(events, "!test:matrix.org")
        assert test_room.federated is True  # Default per spec
        
    def test_guest_access_default(self):
        """Test guest access defaults to False"""
        test_room = room([], "!test:matrix.org")
        assert test_room.guestAccess is False  # Default
        
    def test_guest_access_can_join(self):
        """Test guest access with can_join"""
        events = [{
            "type": "m.room.guest_access",
            "content": {"guest_access": "can_join"}
        }]
        
        test_room = room(events, "!test:matrix.org")
        assert test_room.guestAccess is True
        
    def test_guest_access_forbidden(self):
        """Test guest access with forbidden"""
        events = [{
            "type": "m.room.guest_access",
            "content": {"guest_access": "forbidden"}
        }]
        
        test_room = room(events, "!test:matrix.org")
        assert test_room.guestAccess is False


class TestRoomMemberHandling:
    """Test room member event handling edge cases"""
    
    def test_member_join_with_user_id(self):
        """Test member join event with user_id field"""
        events = [{
            "type": "m.room.member",
            "content": {"membership": "join"},
            "user_id": "@user:matrix.org",
            "state_key": "@user:matrix.org"
        }]
        
        test_room = room(events, "!test:matrix.org")
        assert "@user:matrix.org" in test_room.members
        
    def test_member_join_without_user_id(self):
        """Test member join event without user_id field (invited rooms)"""
        events = [{
            "type": "m.room.member",
            "content": {"membership": "join"},
            "state_key": "@user:matrix.org"
            # No user_id field
        }]
        
        test_room = room(events, "!test:matrix.org")
        assert "@user:matrix.org" in test_room.members
        
    def test_member_leave(self):
        """Test member leave event"""
        events = [{
            "type": "m.room.member",
            "content": {"membership": "leave"},
            "user_id": "@user:matrix.org",
            "state_key": "@user:matrix.org"
        }]
        
        test_room = room(events, "!test:matrix.org")
        assert "@user:matrix.org" in test_room.left
        
    def test_member_invite(self):
        """Test member invite event"""
        events = [{
            "type": "m.room.member",
            "content": {"membership": "invite"},
            "state_key": "@invited:matrix.org"
        }]
        
        test_room = room(events, "!test:matrix.org")
        assert "@invited:matrix.org" in test_room.invited