from pydantic import BaseModel, Field, field_validator, PrivateAttr
from typing import Optional, Dict, Any, Union, List
from halcyon.enums import msgType
from halcyon.security import get_nested_config, get_message_config, get_security_mode


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


class FileThumbnail(BaseModel):
    """File thumbnail metadata"""
    model_config = get_nested_config()
    
    size: Optional[int] = None
    mimetype: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None
    url: Optional[str] = None
    file: Optional[Dict[str, Any]] = None  # Encrypted file reference
    _raw: Optional[Dict[str, Any]] = PrivateAttr(default_factory=dict)
    
    def __init__(self, raw_content: Optional[Dict[str, Any]] = None, 
                 thumbnailURL: Optional[str] = None, 
                 thumbnailFile: Optional[Dict[str, Any]] = None, **kwargs):
        if raw_content:
            super().__init__(
                size=raw_content.get("size"),
                mimetype=raw_content.get("mimetype"),
                height=raw_content.get("h"),
                width=raw_content.get("w"),
                url=thumbnailURL,
                file=thumbnailFile,
                **kwargs
            )
            self._raw = raw_content
        else:
            super().__init__(
                url=thumbnailURL,
                file=thumbnailFile,
                **kwargs
            )
            self._raw = {}
    
    def __bool__(self):
        return bool(self._raw) or any([self.size, self.mimetype, self.height, self.width, self.url, self.file])


class FileInfo(BaseModel):
    """File metadata for attachments"""
    model_config = get_nested_config()
    
    size: Optional[int] = None
    duration: Optional[int] = None  # Duration in milliseconds
    mimetype: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None
    thumbnail: Optional[FileThumbnail] = None
    _raw: Optional[Dict[str, Any]] = PrivateAttr(default_factory=dict)
    
    def __init__(self, raw_content: Optional[Dict[str, Any]] = None, **kwargs):
        if raw_content:
            thumbnail = FileThumbnail(
                raw_content.get("thumbnail_info"),
                thumbnailURL=raw_content.get("thumbnail_url"),
                thumbnailFile=raw_content.get("thumbnail_file")
            ) if raw_content.get("thumbnail_info") or raw_content.get("thumbnail_url") or raw_content.get("thumbnail_file") else None
            
            super().__init__(
                size=raw_content.get("size"),
                duration=raw_content.get("duration"),
                mimetype=raw_content.get("mimetype"),
                height=raw_content.get("h"),
                width=raw_content.get("w"),
                thumbnail=thumbnail,
                **kwargs
            )
            self._raw = raw_content
        else:
            super().__init__(**kwargs)
            self._raw = {}
    
    def __bool__(self):
        return bool(self._raw)


class MessageContent(BaseModel):
    """Matrix message content with support for all message types"""
    model_config = get_nested_config(populate_by_name=True)
    
    # Core fields (all message types)
    type: Optional[msgType] = Field(None, alias="msgtype")
    body: Optional[str] = None
    
    # Text formatting fields
    format: Optional[str] = None
    formattedBody: Optional[str] = Field(None, alias="formatted_body")
    
    # File/media fields
    url: Optional[str] = None
    file: Optional[Dict[str, Any]] = None  # Encrypted file data
    filename: Optional[str] = None  # Original filename
    info: Optional[FileInfo] = None
    
    # Location fields
    geo_uri: Optional[str] = None
    
    # Server notice fields
    server_notice_type: Optional[str] = None
    admin_contact: Optional[str] = None
    limit_type: Optional[str] = None
    
    # Key verification fields
    from_device: Optional[str] = None
    methods: Optional[List[str]] = None
    to: Optional[str] = None
    
    _raw: Optional[Dict[str, Any]] = PrivateAttr(default_factory=dict)
    
    @field_validator('type')
    @classmethod
    def validate_msgtype(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return msgType(v)
        return v
    
    def __init__(self, raw_content: Optional[Dict[str, Any]] = None, **kwargs):
        if raw_content:
            super().__init__(
                type=raw_content.get("msgtype"),
                body=raw_content.get("body"),
                format=raw_content.get("format"),
                formattedBody=raw_content.get("formatted_body"),
                url=raw_content.get("url"),
                file=raw_content.get("file"),
                filename=raw_content.get("filename"),
                info=FileInfo(raw_content.get("info")) if raw_content.get("info") else None,
                geo_uri=raw_content.get("geo_uri"),
                server_notice_type=raw_content.get("server_notice_type"),
                admin_contact=raw_content.get("admin_contact"),
                limit_type=raw_content.get("limit_type"),
                from_device=raw_content.get("from_device"),
                methods=raw_content.get("methods"),
                to=raw_content.get("to"),
                **kwargs
            )
            self._raw = raw_content
            
            # Handle lax mode - store extra fields dynamically
            if get_security_mode() == 'lax':
                known_fields = {'msgtype', 'body', 'format', 'formatted_body', 'url', 'file', 'filename', 'info', 
                               'geo_uri', 'server_notice_type', 'admin_contact', 'limit_type', 'from_device', 'methods', 'to'}
                for key, value in raw_content.items():
                    if key not in known_fields:
                        # Use __dict__ directly to bypass Pydantic's field validation
                        self.__dict__[key] = value
        else:
            super().__init__(**kwargs)
            self._raw = {}
    
    def __bool__(self):
        return bool(self._raw)


class Relates(BaseModel):
    """Message relations (replies, edits, reactions)"""
    model_config = get_nested_config()
    
    type: Optional[str] = None
    eventID: Optional[str] = None
    _raw: Optional[Dict[str, Any]] = PrivateAttr(default_factory=dict)
    
    def __init__(self, raw_content: Optional[Dict[str, Any]] = None, **kwargs):
        if raw_content:
            super().__init__(
                type=raw_content.get("rel_type"),
                eventID=raw_content.get("event_id"),
                **kwargs
            )
            self._raw = raw_content
        else:
            super().__init__(**kwargs)
            self._raw = {}
    
    def __bool__(self):
        return bool(self._raw)


class Message(BaseModel):
    """Matrix message event"""
    model_config = get_message_config()
    
    type: Optional[str] = None
    sender: Optional[str] = None
    origin_server_ts: Optional[int] = None
    event: Optional[IdReturn] = None
    content: Optional[MessageContent] = None
    edit: Optional[MessageContent] = None
    relates: Optional[Relates] = None
    room: Optional[Any] = None  # Associated room object
    _raw: Optional[Dict[str, Any]] = PrivateAttr(default_factory=dict)
    _hasData: bool = PrivateAttr(default=False)
    
    def __init__(self, rawMessage: Optional[Dict[str, Any]] = None, room=None, **kwargs):
        if rawMessage:
            # Parse the message
            event_obj = IdReturn(rawMessage.get("event_id"))
            content_obj = MessageContent(rawMessage.get("content"))
            edit_obj = MessageContent(rawMessage.get("content", {}).get("m.new_content")) if rawMessage.get("content", {}).get("m.new_content") else None
            relates_obj = Relates(rawMessage.get("content", {}).get("m.relates_to")) if rawMessage.get("content", {}).get("m.relates_to") else None
            
            super().__init__(
                type=rawMessage.get("type"),
                sender=rawMessage.get("sender"),
                origin_server_ts=rawMessage.get("origin_server_ts"),
                event=event_obj,
                content=content_obj,
                edit=edit_obj,
                relates=relates_obj,
                room=room,
                **kwargs
            )
            self._raw = rawMessage
            self._hasData = True
        else:
            super().__init__(room=room, **kwargs)
            self._raw = {}
            self._hasData = False
    
    def __bool__(self):
        return self._hasData


# Create compatibility aliases for the old nested class structure
message = Message
message.messageContent = MessageContent
message.idReturn = IdReturn
message.relates = Relates
MessageContent.fileInfo = FileInfo
FileInfo.fileThumbnail = FileThumbnail