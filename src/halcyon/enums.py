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

class Basepath(str, enum.Enum):
    CLIENT = "_matrix/client/r0"
    CLIENT_UNSTABLE = "_matrix/client/unstable"
    MEDIA = "_matrix/media/r0"
    SYNAPSE_ADMIN = "_synapse/admin"

class Presence(str, enum.Enum):
    #When set to "unavailable", the client is marked as being idle
    OFFLINE = "offline"
    ONLINE = "online"
    UNAVAILABLE = "unavailable"


class memberStatus(str, enum.Enum):
    INVITE = "invite"
    JOIN = "join"
    LEAVE = "leave"
    BAN = "ban"
    KNOCK = "knock"