"""
    A object for rooms. Handles event lists.
    Supported:
        m.room.create
        m.room.join_rules
        m.room.name
        m.room.topic
        m.room.related_groups
        m.room.guest_access
        m.room.history_visibility
        m.room.server_acl
        m.room.encryption
    Partially:
        m.room.avatar
        m.room.canonical_alias
        m.room.aliases
        m.room.power_levels (could probably be fleshed out)
        m.room.member

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
    _raw: Optional[Dict[str, Any]] = PrivateAttr(default=None)
    
    def __init__(self, raw_content: Optional[Dict[str, Any]] = None, **kwargs):
        if raw_content:
            super().__init__(
                url=raw_content.get("url"),
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
    
    # m.room.join_rules
    joinRule: Optional[str] = None
    
    # m.room.name
    name: Optional[str] = None
    
    # m.room.topic
    topic: Optional[str] = None
    
    # m.room.aliases and m.room.canonical_alias
    alias: Optional[RoomAlias] = None
    
    # m.room.avatar
    avatar: Optional[RoomAvatar] = None
    
    # m.room.member
    members: List[str] = []
    left: List[str] = []
    invited: List[str] = []
    
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
        
        for event in rawEvents:
            event_type = event.get("type")
            content = event.get("content", {})
            
            if event_type == "m.room.create":
                self.creator = content.get("creator")
                self.version = content.get("room_version", 1)  # default to 1 per spec
                self.federated = content.get("m.federate", True)  # default to true per spec
                if content.get("predecessor"):
                    self.predecessor = RoomPredecessor(content.get("predecessor"))
            
            elif event_type == "m.room.join_rules":
                self.joinRule = content.get("join_rule")
            
            elif event_type == "m.room.name":
                self.name = content.get("name")
            
            elif event_type == "m.room.topic":
                self.topic = content.get("topic")
            
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
                if membership == "join":
                    # catch for no user_id in join events for invited rooms
                    user_id = event.get("user_id") or event.get("state_key")
                    if user_id:
                        members.append(user_id)
                elif membership == "leave":
                    if event.get("user_id"):
                        left.append(event.get("user_id"))
                elif membership == "invite":
                    if event.get("state_key"):
                        invited.append(event.get("state_key"))
            
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