
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
        self.alias = None

        #m.room.avatar
        self.avatar = None

        #m.room.member
        self.members = []

        #m.room.power_levels
        self.permissions = None

        #m.room.related_groups
        self.relatedGroups = []

        #m.room.guest_access
        self.guestAccess = False

        #m.room.history_visibility
        self.historyVisibility = None

        #m.room.server_acl
        self.acl = None

        #m.room.encryption
        self.encryption = None

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

                #These should be EOL
                #if event["type"] == "m.room.aliases":
                #    self.aliases.extend(event["content"].get("aliases", []))

                if event["type"] == "m.room.canonical_alias":
                    self.alias = self.room_alias(event["content"])

                if event["type"] == "m.room.avatar":
                    self.avatar = self.room_avatar(event["content"])

                if event["type"] == "m.room.related_groups":
                    self.relatedGroups.extend(event["content"].get("groups", []))

                if event["type"] == "m.room.guest_access":
                    #This defaults to false, and is only true if can_join is explictly set
                    self.guestAccess = (event["content"].get("guest_access") == "can_join")

                if event["type"] == "m.room.history_visibility":
                    self.historyVisibility = event["content"].get("history_visibility")

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
                    self.permissions = self.roomPermissions(event["content"])

                if event["type"] == "m.room.server_acl":
                    self.acl = self.room_server_acl(event["content"])

                if event["type"] == "m.room.encryption":
                    self.encryption = self.room_encryption(event["content"])


    def __bool__(self):
        return self._hasData

    class roomPredecessor(object):
        def __init__(self, rawContent=None):
            self.event = None
            self.room = None
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
            #matrix defaults
            self.administrator_value = None
            self.moderator_value = None
            self.user_value = None
            self.events_value = None
            self.state_value = None
            self.m_event_values = None

            #synthetic
            self.administrators = None
            self.moderators = None
            self.users = None

            #actions
            self.invite = None
            self.redact = None
            self.ban = None
            self.kick = None

            self._raw = rawContent
            self._hasData = False

            if rawContent:
                self._parseRawContent(rawContent)


        def _parseRawContent(self, rawContent):
            """
                {
                      "events": {
                        "m.room.avatar": 50,
                        "im.vector.modular.widgets": 50,
                        "m.room.history_visibility": 100,
                        "m.room.name": 50,
                        "m.room.server_acl": 100,
                        "m.room.tombstone": 100,
                        "m.room.encryption": 100,
                        "m.room.canonical_alias": 50,
                        "m.room.power_levels": 100,
                        "m.room.topic": 50,
                        "m.space.child": 50
                      }
                    }
            """
            #matrix defaults
            self.administrator_value = 100#used for synthetic
            self.moderator_value = 50
            self.user_value = rawContent.get("users_default")#recomended 0
            self.events_value = rawContent.get("events_default")#rec 0
            self.state_value = rawContent.get("state_default")#rec 50
            self.m_event_values = rawContent.get("events")#its that big dict of m.room.avatar etc

            #synthetic
            self.administrators = {k:v for (k,v) in rawContent["users"].items() if v==self.administrator_value}
            self.moderators = {k:v for (k,v) in rawContent["users"].items() if v==self.moderator_value}
            self.users = rawContent.get("users")#everyone

            #actions
            self.invite = rawContent.get("invite")
            self.redact = rawContent.get("redact")
            self.ban = rawContent.get("ban")
            self.kick = rawContent.get("kick")

            self._hasData = True

        def __bool__(self):
            return self._hasData

    class room_server_acl(object):
        """
            server_acl's might not be specified in every room
        """
        def __init__(self, rawContent=None):
            self.allow_ip_literals = None
            self.allow = None
            self.deny = None

            self._raw = rawContent
            self._hasData = False

            if rawContent:
                self._parseRawContent(rawContent)


        def _parseRawContent(self, rawContent):

            self.allow_ip_literals = rawContent.get("allow_ip_literals")
            self.allow = rawContent.get("allow", [])
            self.deny = rawContent.get("deny", [])
            self._hasData = True

        def __bool__(self):
            return self._hasData


    class room_encryption(object):
        def __init__(self, rawContent=None):
            self.algorithm = None
            self.rotation_period_ms = None
            self.rotation_period_msgs = None
            self._raw = rawContent
            self._hasData = False

            if rawContent:
                self._parseRawContent(rawContent)


        def _parseRawContent(self, rawContent):
            """
                "algorithm": "m.megolm.v1.aes-sha2"
                "rotation_period_ms": 604800000,
                "rotation_period_msgs": 100
            """

            self.algorithm = rawContent.get("algorithm")
            self.rotation_period_ms = rawContent.get("rotation_period_ms")
            self.rotation_period_msgs = rawContent.get("rotation_period_msgs")
            self._hasData = True

        def __bool__(self):
            return self._hasData


    class room_avatar(object):
        def __init__(self, rawContent=None):
            self.url = None
            self._raw = rawContent
            self._hasData = False

            if rawContent:
                self._parseRawContent(rawContent)


        def _parseRawContent(self, rawContent):
            """
                https://matrix.org/docs/spec/client_server/r0.6.1#m-room-avatar
            """

            self.url = rawContent.get("url")
            self._hasData = True

        def __bool__(self):
            return self._hasData


    class room_alias(object):
        def __init__(self, rawContent=None):
            self.canonical = None
            self.alt = []

            self._raw = rawContent
            self._hasData = False

            if rawContent:
                self._parseRawContent(rawContent)


        def _parseRawContent(self, rawContent):
            """
                https://matrix.org/docs/spec/client_server/r0.6.1#m-room-canonical-alias
            """
            self.canonical = rawContent.get("alias")
            self.alt.extend(rawContent.get("alt_aliases", []))
            self._hasData = True

        def __bool__(self):
            return self._hasData

        #def __list__(self):
        #    if self.canonical:
        #        return self.alt.append(self.canonical)
        #    else:
        #        return self.alt


    class idReturn(object):
        def __init__(self, rawID=None):
            self.id = None
            
            self._hasData = False
            
            if rawID:
                self.id = rawID
                self._hasData = True            

        def __bool__(self):
            return self._hasData