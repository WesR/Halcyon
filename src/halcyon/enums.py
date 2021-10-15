import enum

class msgType(str, enum.Enum):
     TEXT = "m.text"
     EMOTE = "m.emote"
     NOTICE = "m.notice"
     IMAGE = "m.image"
     FILE = "m.file"
     AUDIO = "m.audio"
     LOCATION = "m.location"
     VIDEO = "m.video"