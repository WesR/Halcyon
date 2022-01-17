
"""
    A object for rooms. Handles event lists.
    Supported:
        m.room.create
        m.room.join_rules
        m.room.name
        m.room.topic
    Partially:
        m.room.avatar
        m.room.canonical_alias
        m.room.aliases
        m.room.power_levels

    TODO:
        m.room.guest_access
        m.room.related_groups
        m.room.server_acl
        m.room.member
        m.room.history_visibility

        m.room.encryption
        m.room.avatar (ImageInfo and ThumbnailInfo support)


    Theory: have a room full and room minimal, because you don't normally need to waste the time parsing all this
"""

class room(object):
    def __init__(self, rawEvents=None, roomID=None):
        self._rawEvents = rawEvents
        self._hasData = False
        self.id = roomID

        #m.room.create
        self.creator = None
        self.version = None
        self.federated = None
        self.predecessor = None

        #m.room.join_rules
        self.joinRule = None

        #m.room.name
        self.name = None

        #m.room.topic
        self.topic = None

        #m.room.aliases and m.room.canonical_alias
        self.aliases = []

        #m.room.avatar
        self.avatarURL = None

        #m.room.member
        self.members = []

        #m.room.power_levels
        self.permissions = None


        if rawEvents:
            for event in rawEvents:
                if event["type"] == "m.room.create":
                    self.creator = event["content"].get("creator")
                    self.version = event["content"].get("room_version", 1)#default to 1 per spec
                    self.federated = event["content"].get("m.federate", True)#default to true per spec
                    self.predecessor = self.roomPredecessor(event["content"].get("predecessor"))
                
                if event["type"] == "m.room.join_rules":
                    self.joinRule = event["content"].get("join_rule")

                if event["type"] == "m.room.name":
                    self.name = event["content"].get("name")

                if event["type"] == "m.room.topic":
                    self.topic = event["content"].get("topic")
                    #In the future this could be cleaned up so we keep a list of old topics and their replaces

                if event["type"] == "m.room.aliases":
                    self.aliases += event["content"].get("aliases", [])

                if event["type"] == "m.room.canonical_alias":
                    self.aliases += event["content"].get("alias", [])
                    self.aliases += event["content"].get("alt_aliases", [])

                if event["type"] == "m.room.avatar":
                    self.avatarURL = event["content"].get("url")

                if event["type"] == "m.room.member":
                    """
                      room.members (just joined) ??
                      room.members.invited
                      room.members.banned
                      room.members.leave
                    """
                    if event["content"]["membership"] == "join":
                        self.members.append(event["user_id"])

                if event["type"] == "m.room.power_levels":
                    self.predecessor = self.roomPermissions(event["content"])

    def __bool__(self):
        return self._hasData

    class roomPredecessor(object):
        def __init__(self, rawContent=None):
            self.eventID = None
            self.roomID = None
            self._raw = rawContent
            self._hasData = False

            if rawContent:
                self._parseRawContent(rawContent)


        def _parseRawContent(self, rawContent):
            """
                "event_id": "$something:example.org",
                "room_id": "!oldroom:example.org"
            """

            self.event = idReturn(rawContent.get("event_id"))
            self.room = idReturn(rawContent.get("room_id"))
            self._hasData = True

        def __bool__(self):
            return self._hasData


    class roomPermissions(object):
        def __init__(self, rawContent=None):

            self.administrator_value = 100

            #synthetic
            self.administrators = {k:v for (k,v) in rawContent["users"].items() if v==100}
            self.moderators


            self._raw = rawContent
            self._hasData = False

            if rawContent:
                self._parseRawContent(rawContent)


        def _parseRawContent(self, rawContent):
            """
                "event_id": "$something:example.org",
                "room_id": "!oldroom:example.org"
            """

            self.event = idReturn(rawContent.get("event_id"))
            self.room = idReturn(rawContent.get("room_id"))
            self._hasData = True

        def __bool__(self):
            return self._hasData


    class idReturn(object):
        def __init__(self, rawID=None):
            self.id = None
            
            self._hasData = False
            
            if rawID:
                self.id = rawID
                self._hasData = True            

        def __bool__(self):
            return self._hasData