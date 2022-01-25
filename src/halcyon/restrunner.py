import json, enum, uuid, time
import requests
import logging
import io
from halcyon.enums import *

class Runner:
    def __init__(self, homeserver, user_id=None, access_token=None, device_id=None):
        '''
            This class contains all the REST methods to talk to the homeserver

            @param homeserver String the homeserver to talk to
            @param user_id String OPTIONAL the username to use
            @param access_token String OPTIONAL this is a valid session token to use
            @param device_id String OPTIONAL this is the device randmo ID 
        '''
        if "https://" not in homeserver and "http://" not in homeserver:
            homeserver = "https://" + homeserver

        self.HOMESERVER = homeserver
        self.USER_ID = user_id
        self.access_token = access_token
        self.DEVICE_ID = device_id
        self.SESSION = requests.Session()
        self.TXN_ID = int(str(time.time()).replace(".", ""))

        if homeserver:
            self.HOMESERVER = self._wellknownLookup(homeserver)["m.homeserver"]["base_url"]

    def _request(self, method, endpoint, basepath=None, query=None, payload=None, returnRawContent=None, fileData=None, timeout=None, retryCount=1):
        """
        The request method

        @param method string GET, POST...
        @param endpoint String rest of the https string
        @param basepath enum OPTIONAL The basepath for the request (defaults to client)
        @param query Dict OPTIONAL url query
        @param payload Dict/json OPTIONAL The json payload
        @param returnRawContent OBJ OPTIONAL Used to return the content instead of parsing to json first
        @param fileData OBJ OPTIONAL data payload to send
        @param timeout int() timeout for the http responce
        @param retryCount int OPTIONAL downcount to retry the request until failure
        """

        if not basepath:
            basepath = Basepath.CLIENT

        url = self.HOMESERVER + "/"+ basepath + "/" + endpoint.lstrip("/")

        headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type" : "application/json"
        }

        try:
            resp = self.SESSION.request(method, url, json=payload, headers=headers, params=query, data=fileData, timeout=timeout)
            resp.raise_for_status()
        #except requests.Timeout:
        except:
            if retryCount > 0:
                retryCount = retryCount - 1
                # Adding backoff code here could be good, if we try retrying more then once
                return self._request(method, endpoint, basepath=basepath, query=query, payload=payload, 
                    returnRawContent=returnRawContent, fileData=fileData, retryCount=retryCount)

        if returnRawContent:
            return resp.content
        else:
            try:
                return resp.json()
            except:
                return {} # on failure just default to nothing

    def _get(self, endpoint, basepath=None, query=None, returnRawContent=None, timeout=None):
        """
        @param endpoint String rest of the https string
        @param basepath enum OPTIONAL The basepath for the request (defaults to client)
        @param query Dict OPTIONAL url query
        @param timeout int OPTIONAL set a timeout on the http request
        """
        return self._request(method="GET", endpoint=endpoint, basepath=basepath, query=query, returnRawContent=returnRawContent, timeout=timeout)

    def _post(self, endpoint, basepath=None, query=None, payload=None, fileData=None, timeout=None):
        """
        @param endpoint String rest of the https string
        @param basepath enum OPTIONAL The basepath for the request (defaults to client)
        @param query Dict OPTIONAL url query
        @param payload Dict/json OPTIONAL The json payload
        @param timeout int OPTIONAL set a timeout on the http request
        """
        return self._request(method="POST", endpoint=endpoint, basepath=basepath, query=query, payload=payload, fileData=fileData, timeout=timeout)

    def _put(self, endpoint, basepath=None, query=None, payload=None, timeout=None):
        """
            @param endpoint String rest of the https string
            @param basepath enum OPTIONAL The basepath for the request (defaults to client)
            @param query Dict OPTIONAL url query
            @param payload Dict/json OPTIONAL The json payload
            @param timeout int OPTIONAL set a timeout on the http request
        """
        return self._request(method="PUT", endpoint=endpoint, basepath=basepath, query=query, payload=payload, timeout=timeout)

    def _wellknownLookup(self, homeserver):
        try:
            headers = {
                "Content-Type" : "application/json"
            }
            resp = self.SESSION.get(homeserver + "/.well-known/matrix/client", headers=headers)
            return resp.json()
        except Exception as e:
            logging.error("Wellknown lookup failed, cannot find homeserver")
            raise e

    def _getTXNID(self):
        self.TXN_ID += 1
        return str(self.TXN_ID)

    def _passwordLogin(self, userID, password, deviceID=None, device="Halcyon Bot"):
        '''
            Login using a userID and password

            @param userID String the username
            @param password String the password
            @param deviceID String OPTIONAL the device id to use
            @param device String OPTIONAL the human readable device name
            
            @return json The resp object from the matrix server
        '''
        payload = {
          "type": "m.login.password",
          "identifier": {
            "type": "m.id.user",
            "user": userID
          },
          "password": password,
          "initial_device_display_name": device
        }

        if deviceID:
            payload["device_id"] = deviceID

        url = self.HOMESERVER + "/"+ Basepath.CLIENT + "/login"
        resp = requests.post(url, json=payload)

        loginResp = resp.json()
        if "errcode" in loginResp:
            logging.error("Password Login Error: " + loginResp["error"])
        else:
            self.USER_ID = loginResp["user_id"]
            self.access_token = loginResp["access_token"]
            self.DEVICE_ID = loginResp["device_id"]

        return loginResp


    def revokeAccessToken(self, all=False):
        """
            This invalidates the current access token, or every access token

            @param all Bool revoke all access tokens

            @return dict how the logout went
        """
        if all:
            logging.info("Revoking all access tokens")
            return self._post("logout/all")
        else:
            logging.info("Revoking current access token")
            return self._post("logout")


    def whoami(self):
        '''
        A simple check to see who you are logged in as. Good for ensuring auth
        
        @return userid + deviceID
        '''
        return self._get("account/whoami")


    def getUserPresence(self, userID=None):
        """
        Get the specified users current status / presence info

        @param userID String OPTIONAL the full @username:server.com address to fetch the status of

        @return dict presence object
        """
        """
        {
            "content": {
                "avatar_url": "mxc://localhost:wefuiwegh8742w",
                "currently_active": false,
                "last_active_ago": 2478593,
                "presence": "online",
                "status_msg": "Making cupcakes"
            },
            "sender": "@example:localhost",
            "type": "m.presence"
        }
        """
        if not userID:
            userID = self.USER_ID

        endpoint = "presence/" + userID + "/status"

        return self._get(endpoint=endpoint)


    def setUserPresence(self, presence=None, statusMessage=None):
        """
        Set the current users presence/status info. You can only set your own

        @param presence enum/string OPTIONAL The presence of the bot user
        @param statusMessage String the string to set the current users status to
        """

        if not presence:
            presence = Presence.ONLINE

        payload = {
            "presence" : presence
        }

        if statusMessage:
            payload["status_msg"] = statusMessage

        endpoint = "presence/" + self.USER_ID + "/status"

        return self._put(endpoint=endpoint,payload=payload)

    def joinedRooms(self):
        """
        Get a list of rooms the user is in

        @return return list
        """

        return self._get("joined_rooms")["joined_rooms"]

    def publicRooms(self, server=None, limit=50, since=None):
        """
        Get a list of the public rooms on a server
        
        @param server String OPTIONAL the server to list from. Default homeserver
        @param limit int OPTIONAL Max number of rooms to fetch
        @param since String OPTIONAL a pagnation token, recived as next_batch

        @return dict list with total room count
        """
        if not server:
            server = self.HOMESERVER.strip("https://").strip("http://")

        query = {
            "server" : server,
            "limit" : limit
        }

        if since:
            query["since"] = since

        return self._get("publicRooms", query=query)

    def getRoomVisibility(self, roomID):
        """
            Get info on if a room is visible or not

            @param room String the room ID

            @return dict the visibility 
        """
        endpoint = "directory/list/room/" + roomID
        return self._get(endpoint=endpoint)


    def getRoomState(self, roomID):
        """
            Get all info on a room. Name, alias, joins, leaves...

            @param roomID String
        """

        endpoint = "rooms/" + roomID + "/state"
        return self._get(endpoint=endpoint)

    def getRoomMembers(self, roomID):
        """
            Get all member join/leaves

            @param roomID String
        """
        endpoint = "rooms/" + roomID + "/members"
        return self._get(endpoint=endpoint)


    def joinRoom(self, roomID, serverToJoinThrough=None, thirdPartySigned=None):
        """
            Join a specific room

            @param roomID String the room to join
            @param serverToJoinThrough String OPTIONAL the server to attempt to join the room through.
            @param thirdPartySigned String OPTIONAL A signature of an m.third_party_invite token to prove that this user owns 
                                                    a third party identity which has been invited to the room.

            @return dict the room id joined
        """
        if thirdPartySigned:
            logging.error("We don't support third party signed room joins yet")

        query=None

        if serverToJoinThrough:
            #The servers to attempt to join the room through. One of the servers must be participating in the room.
            query = {
            "server_name" : serverToJoinThrough
            }

        endpoint = "join/" + roomID
        return self._post(endpoint=endpoint, query=query)


    def leaveRoom(self, roomID):
        """
            Leave a room. To stop getting info about the room, also call forgetRoom()
        """

        endpoint = "rooms/" + roomID + "/leave"
        return self._post(endpoint=endpoint)


    def forgetRoom(self, roomID):
        """
            To stop getting any info about a room. Good practice to call, so the server can delete rooms no one is in.
        """

        endpoint = "rooms/" + roomID + "/forget"
        return self._post(endpoint=endpoint)


    def sendTyping(self, roomID, seconds=None, userID=None):
        """
            Send typing notifications to the specified room

            @param roomID String the room ID
            @param seconds int OPTIONAL How many seconds to type for. Set to 0 to stop typing. Defaults to 10 seconds
            @param userID String OPTIONAL The userID of who is typing. Defaults to current user

            @return dict empty on success
        """

        if not userID:
            userID = self.USER_ID

        if not seconds:
            seconds = 10

        endpoint = "rooms/" + roomID + "/typing/" + userID

        if seconds == 0:
            payload = {
                "typing": False
            }
        else:
            payload = {
                "typing": True,
                "timeout": seconds * 1000
            }

        return self._put(endpoint=endpoint, payload=payload)


    def sync(self, serverSideFilter=None, presence=None, since=None, timeout=None):
        """
            The big Sync call
            @param serverSideFilter string filter
            @param presence String presenc for the user. Defaults online
            @param since String ask for every action since this specific pagnation ID
            @param timeout int Ask the server to long poll. 
        """

        if not presence:
            presence = Presence.ONLINE

        query = {
            "presence" : presence
        }

        if serverSideFilter:
            query["filter"] = serverSideFilter

        if since:
            query["since"] = since

        if timeout:
            query["timeout"] = timeout*1000#the server takes miliseconds
            http_request_timeout = (timeout+3)#leave 3 seconds for slow connections

        logging.debug("Starting new poll!")
        return self._get("sync", query=query, timeout=timeout)


    def sendEvent(self, roomID, eventType, eventPayload):
        """
            Send a matrix event

        """
        endpoint = "rooms/" + roomID + "/send/" + eventType + "/" + self._getTXNID()

        return self._put(endpoint=endpoint, payload=eventPayload)


    def sendState(self, roomID, eventType, eventPayload, stateKey=None):
        """
            Send a matrix event

        """
        endpoint = "rooms/" + roomID + "/state/" + eventType

        if stateKey:
            endpoint += "/" + stateKey

        time.time().strip(".")

        return self._put(endpoint=endpoint, payload=eventPayload)


        """

            Media API

        """

    def getMedia(self, serverName, mediaID, allowRemote=True):
        """
            Get the raw media file from matrix as a StringIO

            @param serverName String the server the media is on
            @param mediaID String the ID of the string
            @param allowRemote Bool OPTIONAL Allow the homeserver to download media from remote servers

            @return BytesIO(media)
        """

        query = {
            "allow_remote" : allowRemote
        }

        endpoint = "download/" + serverName + "/" + mediaID
        return io.BytesIO(self._get(endpoint=endpoint, basepath=Basepath.MEDIA, query=query, returnRawContent=True))

    def getMediaFromMXC(self, mxc):
        """
            Download an image from a mxc url
            
            @param mxc String mxc url
            @return BytesIO(media)
        """
        mediaURL = mxc.strip("mxc://").split("/")
        return self.getMedia(serverName=mediaURL[0], mediaID=mediaURL[1])


    def uploadMedia(self, fileData, fileName):
        """
            Download an image from a mxc url
            
            @param mxc String mxc url
            @return BytesIO(media)
        """
        contentType=""

        endpoint = "upload"
        query = {
            "filename" : fileName
        }

        #multipart? https://docs.python-requests.org/en/master/user/advanced/#post-multiple-multipart-encoded-files
        return self._post(endpoint=endpoint, basepath=Basepath.MEDIA, query=query, fileData=fileData)