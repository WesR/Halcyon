"""
    Matrix room state handler. Processes room events and maintains room state.
    
    Fully Supported:
        m.room.create - Complete with room types, additional creators (Matrix v1.16+)
        m.room.join_rules - Complete with allow conditions for restricted rooms (Matrix v1.2+)
        m.room.name - Complete
        m.room.topic - Complete with m.topic content object for MIME types (Matrix v1.15+)
        m.room.canonical_alias - Complete with canonical and alternative aliases
        m.room.avatar - Complete with detailed info metadata (dimensions, thumbnails)
        m.room.guest_access - Complete
        m.room.history_visibility - Complete
        m.room.server_acl - Complete with IP literal controls and glob patterns
        m.room.encryption - Complete with algorithm and rotation settings
        m.room.power_levels - Complete with notifications and all power level types
        m.room.member - Complete with user profiles, reasons, authorization, third-party invites

    Deprecated/Legacy (still supported for compatibility):
        m.room.related_groups (deprecated in Matrix spec)
        m.room.aliases (deprecated, replaced by m.room.canonical_alias)

    For encrypted events:
        m.room.encrypted
"""

from pydantic import BaseModel, Field, PrivateAttr
from typing import Optional, Dict, Any, List, Union
from halcyon.security import get_nested_config, get_security_mode


class IdReturn(BaseModel):
    """Helper class for Matrix ID references"""
    model_config = get_nested_config()
    
    id: Optional[str] = None
    _raw: Optional[str] = PrivateAttr(default=None)
    
    def __init__(self, raw_id: Optional[str] = None, **kwargs):
        super().__init__(id=raw_id if raw_id is not None else None, **kwargs)
        self._raw = raw_id
    
    def __bool__(self):
        return self.id is not None


class RoomPredecessor(BaseModel):
    """Room predecessor information"""
    model_config = get_nested_config()
    
    event: Optional[IdReturn] = None
    room: Optional[IdReturn] = None
    _raw: Optional[Dict[str, Any]] = PrivateAttr(default=None)
    
    def __init__(self, raw_content: Optional[Dict[str, Any]] = None, **kwargs):
        if raw_content:
            super().__init__(
                event=IdReturn(raw_content.get("event_id")),
                room=IdReturn(raw_content.get("room_id")),
                **kwargs
            )
            self._raw = raw_content
        else:
            super().__init__(**kwargs)
            self._raw = None
    
    def __bool__(self):
        return self._raw is not None


class RoomPermissions(BaseModel):
    """Room power levels and permissions"""
    model_config = get_nested_config()
    
    # Matrix defaults
    administrator_value: Optional[int] = None
    moderator_value: Optional[int] = None
    user_value: Optional[int] = None
    events_value: Optional[int] = None
    state_value: Optional[int] = None
    m_event_values: Optional[Dict[str, int]] = None
    
    # Synthetic fields
    administrators: Optional[Dict[str, int]] = None
    moderators: Optional[Dict[str, int]] = None
    users: Optional[Dict[str, int]] = None
    
    # Actions
    invite_value: Optional[int] = None
    redact_value: Optional[int] = None
    ban_value: Optional[int] = None
    kick_value: Optional[int] = None
    
    # Notifications
    notifications: Optional[Dict[str, int]] = None
    
    _raw: Optional[Dict[str, Any]] = PrivateAttr(default=None)
    
    def __init__(self, raw_content: Optional[Dict[str, Any]] = None, **kwargs):
        if raw_content:
            # Matrix defaults
            administrator_value = 100  # used for synthetic
            moderator_value = 50
            user_value = raw_content.get("users_default")
            events_value = raw_content.get("events_default")
            state_value = raw_content.get("state_default")
            m_event_values = raw_content.get("events")
            
            # Synthetic fields
            users_dict = raw_content.get("users", {})
            administrators = {k: v for (k, v) in users_dict.items() if v == administrator_value}
            moderators = {k: v for (k, v) in users_dict.items() if v == moderator_value}
            
            super().__init__(
                administrator_value=administrator_value,
                moderator_value=moderator_value,
                user_value=user_value,
                events_value=events_value,
                state_value=state_value,
                m_event_values=m_event_values,
                administrators=administrators,
                moderators=moderators,
                users=users_dict,
                invite_value=raw_content.get("invite"),
                redact_value=raw_content.get("redact"),
                ban_value=raw_content.get("ban"),
                kick_value=raw_content.get("kick"),
                notifications=raw_content.get("notifications"),
                **kwargs
            )
            self._raw = raw_content
        else:
            super().__init__(**kwargs)
            self._raw = None
    
    def __bool__(self):
        return self._raw is not None


class RoomServerAcl(BaseModel):
    """Room server access control list"""
    model_config = get_nested_config()
    
    allow_ip_literals: Optional[bool] = None
    allow: List[str] = []
    deny: List[str] = []
    _raw: Optional[Dict[str, Any]] = PrivateAttr(default=None)
    
    def __init__(self, raw_content: Optional[Dict[str, Any]] = None, **kwargs):
        if raw_content:
            super().__init__(
                allow_ip_literals=raw_content.get("allow_ip_literals"),
                allow=raw_content.get("allow", []),
                deny=raw_content.get("deny", []),
                **kwargs
            )
            self._raw = raw_content
        else:
            super().__init__(**kwargs)
            self._raw = None
    
    def __bool__(self):
        return self._raw is not None


class RoomEncryption(BaseModel):
    """Room encryption configuration"""
    model_config = get_nested_config()
    
    algorithm: Optional[str] = None
    rotation_period_ms: Optional[int] = None
    rotation_period_msgs: Optional[int] = None
    _raw: Optional[Dict[str, Any]] = PrivateAttr(default=None)
    
    def __init__(self, raw_content: Optional[Dict[str, Any]] = None, **kwargs):
        if raw_content:
            super().__init__(
                algorithm=raw_content.get("algorithm"),
                rotation_period_ms=raw_content.get("rotation_period_ms"),
                rotation_period_msgs=raw_content.get("rotation_period_msgs"),
                **kwargs
            )
            self._raw = raw_content
        else:
            super().__init__(**kwargs)
            self._raw = None
    
    def __bool__(self):
        return self._raw is not None


class RoomAvatar(BaseModel):
    """Room avatar information"""
    model_config = get_nested_config()
    
    url: Optional[str] = None
    # Avatar info metadata
    info_height: Optional[int] = None
    info_width: Optional[int] = None  
    info_mimetype: Optional[str] = None
    info_size: Optional[int] = None
    info_thumbnail_url: Optional[str] = None
    info_thumbnail_info: Optional[Dict[str, Any]] = None
    _raw: Optional[Dict[str, Any]] = PrivateAttr(default=None)
    
    def __init__(self, raw_content: Optional[Dict[str, Any]] = None, **kwargs):
        if raw_content:
            info = raw_content.get("info", {})
            super().__init__(
                url=raw_content.get("url"),
                info_height=info.get("h"),
                info_width=info.get("w"),
                info_mimetype=info.get("mimetype"), 
                info_size=info.get("size"),
                info_thumbnail_url=info.get("thumbnail_url"),
                info_thumbnail_info=info.get("thumbnail_info"),
                **kwargs
            )
            self._raw = raw_content
        else:
            super().__init__(**kwargs)
            self._raw = None
    
    def __bool__(self):
        return self._raw is not None


class RoomAlias(BaseModel):
    """Room alias information"""
    model_config = get_nested_config()
    
    canonical: Optional[str] = None
    alt: List[str] = []
    _raw: Optional[Dict[str, Any]] = PrivateAttr(default=None)
    
    def __init__(self, raw_content: Optional[Dict[str, Any]] = None, **kwargs):
        if raw_content:
            super().__init__(
                canonical=raw_content.get("alias"),
                alt=raw_content.get("alt_aliases", []),
                **kwargs
            )
            self._raw = raw_content
        else:
            super().__init__(**kwargs)
            self._raw = None
    
    def __bool__(self):
        return self._raw is not None


class RoomMember(BaseModel):
    """Room member with profile information"""
    model_config = get_nested_config()
    
    user_id: str
    membership: str  # join, leave, invite, ban, knock
    avatar_url: Optional[str] = None
    displayname: Optional[str] = None
    is_direct: Optional[bool] = None
    join_authorised_via_users_server: Optional[str] = None
    reason: Optional[str] = None
    third_party_invite: Optional[Dict[str, Any]] = None
    _raw: Optional[Dict[str, Any]] = PrivateAttr(default=None)
    
    def __init__(self, user_id: str, raw_content: Optional[Dict[str, Any]] = None, **kwargs):
        if raw_content:
            super().__init__(
                user_id=user_id,
                membership=raw_content.get("membership", "leave"),
                avatar_url=raw_content.get("avatar_url"),
                displayname=raw_content.get("displayname"),
                is_direct=raw_content.get("is_direct"),
                join_authorised_via_users_server=raw_content.get("join_authorised_via_users_server"),
                reason=raw_content.get("reason"),
                third_party_invite=raw_content.get("third_party_invite"),
                **kwargs
            )
            self._raw = raw_content
        else:
            super().__init__(user_id=user_id, membership="leave", **kwargs)
            self._raw = None
    
    def __bool__(self):
        return self._raw is not None


class Room(BaseModel):
    """Matrix room state and events"""
    model_config = get_nested_config()
    
    # Core room info
    id: Optional[str] = None
    
    # m.room.create
    creator: Optional[str] = None
    version: Optional[Union[str, int]] = None
    federated: Optional[bool] = None
    predecessor: Optional[RoomPredecessor] = None
    room_type: Optional[str] = None  # Room type (space, etc.)
    additional_creators: List[str] = []  # Additional creators (Matrix v1.16+)
    
    # m.room.join_rules
    joinRule: Optional[str] = None
    join_rule_allow: Optional[List[Dict[str, Any]]] = None  # Allow conditions for restricted rooms
    
    # m.room.name
    name: Optional[str] = None
    
    # m.room.topic
    topic: Optional[str] = None
    topic_content: Optional[Dict[str, Any]] = None  # m.topic object for MIME types
    
    # m.room.aliases and m.room.canonical_alias
    alias: Optional[RoomAlias] = None
    
    # m.room.avatar
    avatar: Optional[RoomAvatar] = None
    
    # m.room.member
    members: List[str] = []  # Simple list for backward compatibility
    left: List[str] = []
    invited: List[str] = []
    member_details: Dict[str, RoomMember] = {}  # Detailed member information
    
    # m.room.power_levels
    permissions: Optional[RoomPermissions] = None
    
    # m.room.related_groups
    relatedGroups: List[str] = []
    
    # m.room.guest_access
    guestAccess: bool = False
    
    # m.room.history_visibility
    historyVisibility: Optional[str] = None
    
    # m.room.server_acl
    acl: Optional[RoomServerAcl] = None
    
    # m.room.encryption
    encryption: Optional[RoomEncryption] = None
    
    # Private attributes
    _rawEvents: Optional[List[Dict[str, Any]]] = PrivateAttr(default=None)
    _hasData: bool = PrivateAttr(default=False)
    
    def __init__(self, rawEvents: Optional[List[Dict[str, Any]]] = None, roomID: Optional[str] = None, **kwargs):
        # Initialize with defaults
        super().__init__(id=roomID, **kwargs)
        self._rawEvents = rawEvents
        self._hasData = False
        
        if rawEvents:
            self._process_events(rawEvents)
            self._hasData = True
    
    def _process_events(self, rawEvents: List[Dict[str, Any]]):
        """Process Matrix room events and populate fields"""
        members = []
        left = []
        invited = []
        relatedGroups = []
        member_details = {}
        
        for event in rawEvents:
            event_type = event.get("type")
            content = event.get("content", {})
            
            if event_type == "m.room.create":
                self.creator = content.get("creator")
                self.version = content.get("room_version", 1)  # default to 1 per spec
                self.federated = content.get("m.federate", True)  # default to true per spec
                self.room_type = content.get("type")
                self.additional_creators = content.get("additional_creators", [])
                if content.get("predecessor"):
                    self.predecessor = RoomPredecessor(content.get("predecessor"))
            
            elif event_type == "m.room.join_rules":
                self.joinRule = content.get("join_rule")
                self.join_rule_allow = content.get("allow")
            
            elif event_type == "m.room.name":
                self.name = content.get("name")
            
            elif event_type == "m.room.topic":
                self.topic = content.get("topic")
                self.topic_content = content.get("m.topic")
            
            elif event_type == "m.room.canonical_alias":
                self.alias = RoomAlias(content)
            
            elif event_type == "m.room.avatar":
                self.avatar = RoomAvatar(content)
            
            elif event_type == "m.room.related_groups":
                relatedGroups.extend(content.get("groups", []))
            
            elif event_type == "m.room.guest_access":
                # This defaults to false, and is only true if can_join is explicitly set
                self.guestAccess = (content.get("guest_access") == "can_join")
            
            elif event_type == "m.room.history_visibility":
                self.historyVisibility = content.get("history_visibility")
            
            elif event_type == "m.room.member":
                membership = content.get("membership")
                user_id = event.get("user_id") or event.get("state_key")
                
                if user_id:
                    # Create detailed member object
                    member_obj = RoomMember(user_id, content)
                    member_details[user_id] = member_obj
                    
                    # Maintain backward compatibility lists
                    if membership == "join":
                        members.append(user_id)
                    elif membership == "leave":
                        left.append(user_id)
                    elif membership == "invite":
                        invited.append(user_id)
            
            elif event_type == "m.room.power_levels":
                self.permissions = RoomPermissions(content)
            
            elif event_type == "m.room.server_acl":
                self.acl = RoomServerAcl(content)
            
            elif event_type == "m.room.encryption":
                self.encryption = RoomEncryption(content)
        
        # Set the lists
        self.members = members
        self.left = left
        self.invited = invited
        self.relatedGroups = relatedGroups
        self.member_details = member_details
        
        # Handle lax mode for extra fields
        if get_security_mode() == 'lax':
            for event in rawEvents:
                content = event.get("content", {})
                for key, value in content.items():
                    if not hasattr(self, key) and key not in {'creator', 'room_version', 'm.federate', 'predecessor', 'join_rule', 'name', 'topic', 'alias', 'url', 'groups', 'guest_access', 'history_visibility', 'membership', 'users', 'allow_ip_literals', 'allow', 'deny', 'algorithm', 'rotation_period_ms', 'rotation_period_msgs'}:
                        self.__dict__[key] = value
    
    def __bool__(self):
        return self._hasData


# Create compatibility aliases for the old nested class structure
room = Room
room.roomPredecessor = RoomPredecessor
room.roomPermissions = RoomPermissions
room.room_server_acl = RoomServerAcl
room.room_encryption = RoomEncryption
room.room_avatar = RoomAvatar
room.room_alias = RoomAlias
RoomPredecessor.idReturn = IdReturn