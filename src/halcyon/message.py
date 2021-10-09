
"""
This is the message object that will be created for each message
"""

"""
    m.text
    m.emote
    m.notice
    m.image
    m.file
    m.audio
    m.location
    m.video
"""
class msgType(str, enum.Enum):
     TEXT = "m.text"
     EMOTE = "m.emote"
     NOTICE = "m.notice"
     IMAGE = "m.image"
     FILE = "m.file"
     AUDIO = "m.audio"
     LOCATION = "m.location"
     VIDEO = "m.video"

class message(object):
    def __init__(self, rawMessage=None, roomID=None):
        self._raw = rawMessage
        self._hasData = False
        self.room = self.idReturn(roomID)#later we flesh these out to return cached room info

        self.type = None
        self.sender = None
        self.origin_server_ts = None
        self.event = self.idReturn(rawMessage["event_id"])
        self.content = self.messageContent(rawMessage["content"])

        #If these exist, they will be set to True and the vals, else false and None
        self.edit = self.messageContent(rawMessage["content"].get("m.new_content"))
        self.relates = self.relates(rawMessage["content"].get("m.relates_to"))

        if rawMessage:
            self._parseRawMessage(rawMessage)


    class idReturn(object):
        def __init__(self, rawID=None):
            self.id = None
            
            self._hasData = False
            
            if rawID:
                self.id = rawID
                self._hasData = True            

        def __bool__(self):
            return self._hasData


    class messageContent(object):
        def __init__(self, rawContent=None):
            self.type = None
            self.body = None
            self.format = None
            self.formattedBody = None

            self.url = None
            self.info = None
            
            self._raw = rawContent
            self._hasData = False
            
            if rawContent:
                self._parseRawContent(rawContent)


        def _parseRawContent(self, rawContent):
            """
                "msgtype": "m.text",
                "body": " * _almost to alpha1_ this works ala #trash:blackline.xyz ",
                "format": "org.matrix.custom.html",
                "formatted_body": " * <em>almost to alpha1</em> this works ala <a href"
            """
            """
                "body": "ima_1de2d8f.jpeg",
                "info": {
                  "size": 2534288,
                  "mimetype": "image/jpeg",
                  "w": 3024,
                  "h": 4032
                },
                "url": "mxc://blackline.xyz/MZANSwsvznNvjxSBksFssgas",
                "msgtype": "m.image"

                "body": "junk",
                "info": {
                  "size": 14155776
                },
                "msgtype": "m.file",
                "url": "mxc://blackline.xyz/kuknpUPzsxjoAeIWiyhXyTsR"
            """
            """
                m.text
                m.emote
                m.notice
                m.image
                m.file
                m.audio
                m.location
                m.video
            """

            self.type = msgType(rawContent.get("msgtype"))
            self.body = rawContent.get("body")
            self.format = rawContent.get("format")
            self.formattedBody = rawContent.get("formatted_body")

            self.url = rawContent.get("url")
            self.info = self.fileInfo(rawMessage.get("info"))
            self._hasData = True

        def __bool__(self):
            return self._hasData

        #def __str__(self):
        #    return self._raw

    class fileInfo(object):
        def __init__(self, rawContent=None):
            self.size = None
            self.mimetype = None
            self.height = None
            self.width = None

            self._raw = rawContent
            self._hasData = False

            if rawContent:
                self._parseRawContent(rawContent)

        def _parseRawContent(self, rawContent):
            """
                "size": 2534288,
                "mimetype": "image/jpeg",
                "w": 3024,
                "h": 4032
            """

            self.size = rawContent.get("size")
            self.mimetype = rawContent.get("mimetype")
            self.height = rawContent.get("h")
            self.width = rawContent.get("w")
            self._hasData = True

        def __bool__(self):
            return self._hasData

    class relates(object):
        def __init__(self, rawContent=None):
            self.type = None
            self.eventID = None

            self._raw = rawContent
            self._hasData = False

            if rawContent:
                self._parseRawContent(rawContent)

        def _parseRawContent(self, rawContent):
            """
                "rel_type": "m.replace",
                "event_id": "$FjpUGjnIe7XYH1oos_eNJLf6pVjn03Xtl1PkixcLCNk"
            """

            self.type = rawContent.get("rel_type")
            self.eventID = rawContent.get("event_id")
            self._hasData = True

        def __bool__(self):
            return self._hasData


    def _parseRawMessage(self, rawMessage):
        """
        {
          "type": "m.room.message",
          "sender": "@gen3:blackline.xyz",
          "content": {
            "msgtype": "m.text",
            "body": "test text event"
          },
          "origin_server_ts": 1632894724739,
          "unsigned": {
            "age": 75364
          },
          "event_id": "$tBqxdcM"
        }
        
        """

        self.type = rawMessage["type"]
        self.sender = rawMessage["sender"]
        self.origin_server_ts = rawMessage["origin_server_ts"]
        self._hasData = True

    def __bool__(self):
        return self._hasData