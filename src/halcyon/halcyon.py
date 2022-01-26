import enum, json, requests, logging, base64
import markdown, re
import asyncio
import time

import functools
import signal

import halcyon.restrunner
from halcyon.message import *
from halcyon.room import *
from halcyon.enums import *

class Client:
    """
        This is the general interface that is exposed to the user
    """
    def __init__(self, loop=None, ignoreFirstSync=True):
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self.logoutOnDeath = False
        self.loopPollInterval = 0.1#seconds
        self.long_poll_timeout = 10#seconds, up this value to be nicer to the server.
        #Bug/Thing I don't like: The client doesn't immediately close when you ctrl^c when you have this value high.
        #This is because requests is blocking, meaning that we have to wait for a return from the sever before we can handle the SIGs

        self.restrunner = None
        self.sinceToken = str()
        self.encryptedCurveCount = 0
        self.ignoreFirstSync = ignoreFirstSync
        self.firstSync = True
        self.revokeSessionTokenOnExit = False

        self.roomCache = dict()

    def _encodeTokenDict(self, tokenDict):
        """
            Return a string encoded for the halcyon Token 

            @param tokenDict Dict the dict to encode

            @return the base64 string
        """
        return str(base64.b64encode(bytes(json.dumps(tokenDict, separators=(',', ':')), "utf-8")), "utf-8")

    def _decodeTokenDict(self, token):
        """
            Returns a dict from a base64 encoded string
            
            @param token String the base64 token to decode

            @return dict
        """

        try:
            return json.loads(str(base64.b64decode(token), "utf-8"))
        except Exception as e:
            print(token)
            logging.error("Cannot decode token dict, double check your token is okay?")
            exit()

    def _generateNewSessionToken(self, userID, password):
        return self.restrunner._passwordLogin(userID, password)

    def _init(self, halcyonToken=None, userID=None, password=None, homeserver=None):
        """
            We support two forms of login, halcyontoken and ol' userid+password. token is prefered, so you don't keep making valid tokens.
            
        """

        if halcyonToken:
            splitToken = halcyonToken.split(".")
            for token in splitToken:
                decodedToken = self._decodeTokenDict(token)

                if decodedToken["typ"] == "engine":
                    homeserver = decodedToken["hsvr"]
                    userID = decodedToken["user"]

                if decodedToken["typ"] == "valid-token":
                    accessToken = decodedToken["token"]
                    deviceID = decodedToken["device_id"]

            self.restrunner = halcyon.restrunner.Runner(homeserver=homeserver, user_id=userID, access_token=accessToken, device_id=deviceID)

            resp = self.restrunner.whoami()
            if "errcode" not in resp:
                return
            else:
                logging.error("error logging in with token")

        if userID and password:
            if homeserver:
                self.restrunner = halcyon.restrunner.Runner(homeserver=homeserver, user_id=userID)
                client._generateNewSessionToken(userID, password)
                self.logoutOnDeath = True
                #TODO: state.json file
                #accepts file location, we write state info there, and load data from it
                #if can write to disk, leave session open
                #else kill session on client unload
                return

        logging.error("No valid login method found. Sudoku")
        exit(1)


    def _roomcacheinit(self, cachePublicRooms=False):
        """
            Build a cache of room info that can be linked into incoming messages
        """
        self.roomCache["cache_age"] = time.time_ns()#nanoseconds since epoch
        self.roomCache["rooms"] = dict()

        joined_rooms = self.restrunner.joinedRooms()
        for roomID in joined_rooms:
            self.roomCache["rooms"][roomID] = room(rawEvents=self.restrunner.getRoomState(roomID), roomID=roomID)

    def _refreshRoomCache(self):
        """
            Used to refresh the room caches existing rooms
        """
        for roomID in self.roomCache["rooms"]:
            self._addRoomToCache(roomID)

    def _addRoomToCache(self, roomID):
        """
            Add a room to the room cache, can be used to refresh an old room cache
        """
        self.roomCache["rooms"][roomID] = room(rawEvents=self.restrunner.getRoomState(roomID), roomID=roomID)


    def _getRoom(self, roomID):
        """
            retrieve a room from the roomcache, caching if it is not already in the cache
            @param roomID String the room ID
        """
        if roomID in self.roomCache["rooms"]:
            return self.roomCache["rooms"][roomID]
        else:
            self._addRoomToCache(roomID)

            #if it doesn't populate, return an empty room
            if roomID in self.roomCache["rooms"]:
                return self.roomCache["rooms"][roomID]
            else:
                return room()

    def _destruction(self):
        if self.logoutOnDeath:
            logging.info("Logging out user")
            logging(str(self._logoutUser()))
        
        logging.info("Stopping main event loop")
        self.loop.stop()


    def _logoutUser(self, revokeAllTokens=False):
        """
            Revoke the specified access token, or all
            
            @param revokeAllTokens Bool Revoke every valid session token, on all devices.
        """

        return self.restrunner.revokeAccessToken(revokeAllTokens)


    async def _homeserverSync(self):

        resp = self.restrunner.sync(since=self.sinceToken, timeout=self.long_poll_timeout)
        if "next_batch" not in resp:#This should catch bad syncs
            return

        self.sinceToken = resp["next_batch"]

        if "device_one_time_keys_count" in resp:
            if "signed_curve25519" in resp["device_one_time_keys_count"]:
                self.encryptedCurveCount = resp["device_one_time_keys_count"]["signed_curve25519"]

        #This is the stopping point so we dont parse messages first sync
        if self.ignoreFirstSync and self.firstSync:
            self.firstSync = False
            return


        # handle resp["presence"] events

        # handle room events

        # handle room messages

        if "rooms" in resp:
            #events for rooms you are in
            if "join" in resp["rooms"]:
                for roomID in resp["rooms"]["join"]:
                    if "timeline" in resp["rooms"]["join"][roomID]:
                        if "events" in resp["rooms"]["join"][roomID]["timeline"]:
                            for event in resp["rooms"]["join"][roomID]["timeline"]["events"]:
                                if event["type"] == "m.room.message":
                                    #support asyncio.create_task( ?
                                    newMsg = message(event, self._getRoom(roomID))
                                    if newMsg.edit:
                                        await self.on_message_edit(newMsg)
                                    else:
                                        await self.on_message(newMsg)

            if "invite" in resp["rooms"]:
                for roomID in resp["rooms"]["invite"]:
                    if "invite_state" in resp["rooms"]["invite"][roomID]:
                        if "events" in resp["rooms"]["invite"][roomID]["invite_state"]:
                            """
                                For invites, we don't want to handle each event seperatly, since they are not information dense
                                Because of this, we are going to compress the following types inside the room obj
                                m.room.create m.room.join_rules m.room.name m.room.member 
                            """
                            newRoom = room(rawEvents=resp["rooms"]["invite"][roomID]["invite_state"]["events"], roomID=roomID)
                            await self.on_room_invite(newRoom)
                    

            if "leave" in resp["rooms"]:
                for roomID in resp["rooms"]["leave"]:
                    await self.on_room_leave(roomID)

        #print(json.dumps(resp))
        #print(json.dumps(self.restrunner.sync(since=self.sinceToken)))

    async def send_message(self, roomID, body, textFormat=None, replyTo=None, isNotice=False):
        """
            Send a message to a specified room.

            @param roomID String the room to send the message to
            @param body String the text body to send. defaults to plain text
            @param textFormat String OPTIONAL If the string is formatted. Must be "markdown" or "html"
            @param replyTo String OPTIONAL The ID to the event you want to reply to
            @param isNotice bool OPTIONAL Send the message as a notice. slightly grey on desktop.

            @return dict contains 'event_id' of new message
        """
        """
            Supported HTML tags:
            font, del, h1, h2, h3, h4, h5, h6, blockquote, p, a, ul, ol, sup, sub, 
            li, b, i, u, strong, em, strike, code, hr, br, div, table, thead, tbody, 
            tr, th, td, caption, pre, span, img.
        """

        """
        content
            "msgtype": "io.element.effects.space_invaders",
        """
        messageType = "m.text"
        if isNotice:
            messageType = "m.notice"


        if textFormat:
            if textFormat == "markdown":
                formattedBody = markdown.markdown(body)
                body = re.sub('<[^<]+?>', '', formattedBody)

            if textFormat == "html":
                formattedBody = body
                body = re.sub('<[^<]+?>', '', body)

            messageContent = {
                "msgtype": messageType,
                "body": body,
                "format": "org.matrix.custom.html",
                "formatted_body" : formattedBody,
            }
        else:
            messageContent = {
                "msgtype": messageType,
                "body": body
            }


        if replyTo:
            messageContent["m.relates_to"] = {
                "m.in_reply_to": {
                    "event_id": replyTo
                }
            }

        return(self.restrunner.sendEvent(roomID=roomID, eventType="m.room.message", eventPayload=messageContent))
    

    async def send_typing(self, roomID, seconds=None):
        """
            Send a typing event to a room. Useful when doing a lot of work in the background

            @param roomID String the room id that you want to type in
            @param seconds int OPTIONAL How many seconds you want to type for. Default 10
        """
        self.restrunner.sendTyping(roomID, seconds)


    async def send_file(self, roomID, body, replyTo=None):
        """
            Placeholder for the file form of the send_message command
        """
        pass


    async def join_room(self, roomID):
        resp = self.restrunner.joinRoom(roomID)
        self._addRoomToCache(roomID)#update the cache, since we might be able to see more room info
        return resp


    async def change_presence(self, presence=None, statusMessage=None):
        """
            Set the bot presence and status message

            @param presence enum/string OPTIONAL The presence of the bot user
            @param statusMessage String the string to set the current users status to
        """

        #validation for presence value?
        #halcyon.Status.idle

        resp = self.restrunner.setUserPresence(presence=presence, statusMessage=statusMessage)
        # {'errcode': 'M_NOT_JSON', 'error': 'Content not JSON.'}
        if 'errcode' in resp:
            logging.error("Change presence error: " + resp["error"])
    

    #async def get_user_presence(self, userID):
    #    print(self.restrunner.getUserPresence(userID=userID))
    # Include this in a user info/lookup function?


    async def download_media(self, mxc):
        """
            Returns a BytesIO file fetched from an MXC

            @param String MXC url

            @return BytesIO bufffer
        """
        return(self.restrunner.getMediaFromMXC(mxc))

    async def upload_media(self, fileBuffer, fileName):
        """
            Upload a file

            @param file BytesIO object
            @param fileName filename for the object
        """
        return(self.restrunner.uploadMedia(fileData=fileBuffer, fileName=fileName))


    def event(self, coro):
        # Validation we don't need to worry about
        setattr(self, coro.__name__, coro)
        return coro

    async def on_ready(self):
        """on ready stub"""
        pass

    async def on_message(self, message):
        """on message stub"""
        pass

    async def on_message_edit(self, message):
        """on message edit stub"""
        pass

    async def on_room_invite(self, room):
        """on room invite stub. passed room object"""
        pass

    async def on_room_leave(self, roomID):
        """on room leave passes room id"""
        pass

    async def _halcyonMainLoop(self):
        await self.on_ready()
        while True:
            await self._homeserverSync()

            #update room cache every hour
            if (time.time_ns() > (self.roomCache["cache_age"] + 3600000000000)):
                logging.debug("Updating room cache")
                self.roomCache["cache_age"] = time.time_ns()
                self._refreshRoomCache()

            await asyncio.sleep(self.loopPollInterval)

    def run(self, halcyonToken=None, userID=None, password=None, homeserver=None, loopPollInterval=None, longPollTimeout=None):
        
        if loopPollInterval:
            print("loopPollInterval has been deprecated because of superior polling update, please set var 'longPollTimeout' instead.")
            logging.warning("loopPollInterval has been deprecated because of better polling, please set var 'longPollTimeout' instead.")

        if longPollTimeout:
            logging.info("Custom poll value set")
            self.long_poll_timeout = longPollTimeout

        #login
        self._init(halcyonToken, userID, password, homeserver)
        self._roomcacheinit()
        loop = self.loop
        try:
            loop.add_signal_handler(2, lambda: self._destruction())#SIGINT
            loop.add_signal_handler(15, lambda: self._destruction())#SIGTERM
        except NotImplementedError:
            pass

        try:
            loop.create_task(self._halcyonMainLoop())
            loop.run_forever()
        except KeyboardInterrupt:
            logging.info('Keyboard says death')
        finally:
            self._destruction()