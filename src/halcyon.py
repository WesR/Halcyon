import enum, json, requests, time, logging, base64
import argparse
import markdown, re
import asyncio
import time

import functools
import signal

import restrunner
from message import *
from room import *

class Client:
    """
        This is the general interface that is exposed to the user
    """
    def __init__(self, loop=None, ignoreFirstSync=True):
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self.logoutOnDeath = False
        self.loopPollInterval = 7#seconds

        self.restrunner = None
        self.sinceToken = str()#"s168053_9238002_211_518042_38777_66_34968_77975_20"#str()
        self.encryptedCurveCount = 0
        self.ignoreFirstSync = ignoreFirstSync
        self.firstSync = True
        self.revokeSessionTokenOnExit = False

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

            self.restrunner = restrunner.Runner(homeserver=homeserver, user_id=userID, access_token=accessToken, device_id=deviceID)

            resp = self.restrunner.whoami()
            if "errcode" not in resp:
                return
            else:
                logging.error("error logging in with token")

        if userID and password:
            if homeserver:
                self.restrunner = restrunner.Runner(homeserver=homeserver, user_id=userID)
                client._generateNewSessionToken(userID, password)
                self.logoutOnDeath = True
                #TODO: state.json file
                #accepts file location, we write state info there, and load data from it
                #if can write to disk, leave session open
                #else kill session on client unload
                return

        logging.error("No valid login method found. Sudoku")
        exit(1)


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

        resp = self.restrunner.sync(since=self.sinceToken)
        self.sinceToken = resp["next_batch"]

        if "device_one_time_keys_count" in resp:
            if "signed_curve25519" in resp["device_one_time_keys_count"]:
                self.encryptedCurveCount = resp["device_one_time_keys_count"]["signed_curve25519"]

        #This is the stopping point so we dont parse messages first sync
        if self.ignoreFirstSync and self.firstSync:
            self.firstSync = False
            return


        #handle resp["presence"] events

        #handle room events

        #handle room messages

        if "rooms" in resp:
            #events for rooms you are in
            if "join" in resp["rooms"]:
                for roomID in resp["rooms"]["join"]:
                    if "timeline" in resp["rooms"]["join"][roomID]:
                        if "events" in resp["rooms"]["join"][roomID]["timeline"]:
                            for event in resp["rooms"]["join"][roomID]["timeline"]["events"]:
                                if event["type"] == "m.room.message":
                                    #support asyncio.create_task( ?
                                    newMsg = message(event, roomID)
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
                            newRoom = room(resp["rooms"]["invite"][roomID]["invite_state"]["events"], roomID)
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

    async def join_room(self, roomID):
        return(self.restrunner.joinRoom(roomID))

    def event(self, coro):
        # Validation we don't need to worry about
        setattr(self, coro.__name__, coro)
        return coro

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
        while True:
            await self._homeserverSync()
            await asyncio.sleep(self.loopPollInterval)

    def run(self, halcyonToken=None, userID=None, password=None, homeserver=None, loopPollInterval=None):
        
        if loopPollInterval:
            self.loopPollInterval = loopPollInterval

        #login
        self._init(halcyonToken, userID, password, homeserver)
        loop = self.loop
        loop.add_signal_handler(2, lambda: self._destruction())#SIGINT
        loop.add_signal_handler(15, lambda: self._destruction())#SIGTERM

        try:
            loop.create_task(self._halcyonMainLoop())
            loop.run_forever()
        except KeyboardInterrupt:
            logging.info('Keyboard says death')
        finally:
            self._destruction()


if __name__ == "__main__":
    client = Client()

    parser = argparse.ArgumentParser(
        description='By this, you can generate a halcyonToken for your project, \
        for example python3 -m halcyon -H matrix.org -u @kevin:matrix.org -p on&on&on1337',
        epilog="Have fun creating")
    parser.add_argument('-s', '--server', help='Homeserver the user belongs to ex: matrix.org')
    parser.add_argument('-u', '--username', help='Your full username ex: @kevin:matrix.org')
    parser.add_argument('-p', '--password', help='Your full password for your matrix account')
    parser.add_argument('--include-password', action="store_true", help='Save your username and password in the token for reauth (Not required right now since matrix tokens do not expire)')

    parser.add_argument('--decode', help='Decode an existing token')
    parser.add_argument('--pretty', action="store_true", help='Pretty print the decoded token')
    parser.add_argument('--revoke', help='Revoke an existing token')
    parser.add_argument('--revoke-all-tokens', help='Revoke an all existing token')

    args = parser.parse_args()

    if args.decode:
        splitToken = args.decode.split(".")
        if args.pretty:
            [print(json.dumps(client._decodeTokenDict(x), indent=2)) for x in splitToken]
        else:
            [print(json.dumps(client._decodeTokenDict(x))) for x in splitToken]
        exit()


    if args.revoke:
        splitToken = args.revoke.split(".")
        for x in splitToken:
            decodedToken = client._decodeTokenDict(x)
            #We assume that the engine payload is always first... 
            if decodedToken["typ"] == "engine":
                client.restrunner = restrunner.Runner(homeserver=decodedToken["hsvr"])

            if decodedToken["typ"] == "valid-token":
                client.restrunner.access_token = decodedToken["token"]
                if client._logoutUser() == {}:
                    print("Token revoked")
                exit()

    if args.revoke_all_tokens:
        splitToken = args.revoke_all_tokens.split(".")
        for x in splitToken:
            decodedToken = client._decodeTokenDict(x)
            if decodedToken["typ"] == "engine":
                client.restrunner = restrunner.Runner(homeserver=decodedToken["hsvr"])

            if decodedToken["typ"] == "valid-token":
                client.restrunner.access_token = decodedToken["token"]
                resp = client._logoutUser(revokeAllTokens=True)
                if resp == {}:
                    print("Tokens revoked")

                print(resp)
                exit()

    if not args.server:
        print("Please specify a homeserver")
        exit()
    else:
        client.restrunner = restrunner.Runner(homeserver=args.server)

    if args.username and args.password:
        halcyonToken = str()#final token
        
        halcyonToken += client._encodeTokenDict({
                "typ" : "engine",
                "hsvr" : args.server,
                "user" : args.username
            })

        newSessionToken = client._generateNewSessionToken(args.username, args.password)
        halcyonToken += "." + client._encodeTokenDict({
                "typ" : "valid-token",
                "token" : newSessionToken["access_token"],
                "exp" : 0,#not a spec yet
                "device_id" : newSessionToken["device_id"]
            })

        print("Happy hacking!\n")
        print(halcyonToken)
    else:
        print("Please include a username and password")