import json, requests, enum, uuid, time
import logging

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

class Runner:
    def __init__(self, homeserver, user_id=None, access_token=None, device_id=None):
        '''
            This class contains all the REST methods to talk to the homeserver

            @param homeserver String the homeserver to talk to
            @param user_id String OPTIONAL the  username to use
            @param access_token String OPTIONAL this is a valid session token to use
            @param device_id String OPTIONAL this is the device random ID 
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

    def _request(self, method, endpoint, basepath=None, query=None, payload=None):
        """
        The request method

        @param method string GET, POST...
        @param endpoint String rest of the https string
        @param basepath enum OPTIONAL The basepath for the request (defaults to client)
        @param query Dict OPTIONAL url query
        @param payload Dict/json OPTIONAL The json payload
        """

        if not basepath:
            basepath = Basepath.CLIENT

        url = self.HOMESERVER + "/"+ basepath + "/" + endpoint.lstrip("/")

        headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type" : "application/json"
        }

        #print(url)
        #print(str(headers))
        resp = self.SESSION.request(method, url, json=payload, headers=headers, params=query)

        return resp.json()

    def _get(self, endpoint, basepath=None, query=None):
        """
        @param endpoint String rest of the https string
        @param basepath enum OPTIONAL The basepath for the request (defaults to client)
        @param query Dict OPTIONAL url query
        """
        return self._request(method="GET", endpoint=endpoint, basepath=basepath, query=query)

    def _post(self, endpoint, basepath=None, query=None, payload=None):
        """
        @param endpoint String rest of the https string
        @param basepath enum OPTIONAL The basepath for the request (defaults to client)
        @param query Dict OPTIONAL url query
        @param payload Dict/json OPTIONAL The json payload
        """
        return self._request(method="POST", endpoint=endpoint, basepath=basepath, query=query, payload=payload)

    def _put(self, endpoint, basepath=None, query=None, payload=None):
        """
            @param endpoint String rest of the https string
            @param basepath enum OPTIONAL The basepath for the request (defaults to client)
            @param query Dict OPTIONAL url query
            @param payload Dict/json OPTIONAL The json payload
        """
        return self._request(method="PUT", endpoint=endpoint, basepath=basepath, query=query, payload=payload)

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
        """

        endpoint = "rooms/" + roomID + "/state"
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

    def sync(self, serverSideFilter=None, presence=None, since=None):
        """
        big fuc
        s167221_9050551_0_516082_36840_65_33646_75651_20
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

        
        return self._get("sync", query=query)

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