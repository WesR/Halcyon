# Using Halcyon

### CLI usage
halcyon can be called from the CLI to do some management of the account. \
See the help message with `python3 -m halcyon -h`
Right now it can be used to
1. generate a new token
2. decode an existing token
3. revoke a single token
4. revoke all tokens

```
usage: halcyon [-h] [-s SERVER] [-u USERNAME] [-p PASSWORD] [--include-password] [--decode DECODE] [--pretty] [--revoke REVOKE] [--revoke-all-tokens REVOKE_ALL_TOKENS]

By this, you can generate a halcyonToken for your project, for example python3 -m halcyon -s matrix.org -u @kevin:matrix.org -p on&on&on1337

optional arguments:
  -h, --help            show this help message and exit
  -s SERVER, --server SERVER
                        Homeserver the user belongs to ex: matrix.org
  -u USERNAME, --username USERNAME
                        Your full username ex: @kevin:matrix.org
  -p PASSWORD, --password PASSWORD
                        Your full password for your matrix account
  --include-password    Save your username and password in the token for reauth (Not required right now since matrix tokens do not expire)
  --decode DECODE       Decode an existing token that you pass in
  --pretty              Pretty print the decoded token
  --revoke REVOKE       Revoke an existing token
  --revoke-all-tokens REVOKE_ALL_TOKENS
                        Revoke an all existing token for the account

Have fun creating
```

## Example bot
This bot will auto join any room it is invited to, and will reply to the phrase "give me random" with a random string.
```python
import halcyon
import requests, json

client = halcyon.Client()

@client.event
async def on_room_invite(room):
    """On room invite, autojoin and say hello"""
    print("Someone invited us to join " + room.name)
    await client.join_room(room.id)
    await client.send_message(room.id, body="Hello humans")


@client.event
async def on_message(message):
    """If we see a message with the phrase 'give me random', do a reply message with 32 random characters"""
    print(message.event.id)
    if "give me random" in message.content.body:
        await client.send_typing(message.room.id) # This typing notification will let the user know we've seen their message
        body = "This looks random: " + requests.get("https://random.wesring.com").json()["value"]
        await client.send_message(message.room.id, body=body, replyTo=message.event.id)


@client.event
async def on_ready():
    print("Online!")
    await client.change_presence(statusMessage="indexing /dev/urandom")

if __name__ == '__main__':
    client.run(halcyonToken="eyJ0eXAiO...")
```

### Example bots

[Example message bot](./examples/basic_message_bot.py), looks for a phrase and replies with a phrase
[Example image bot](./examples/basic_image_bot.py), looks for a phrase and replies with an image
[Image Archive bot](./examples/image_archive_bot.py), looks for images, and saves them

## halcyon function documentation
+ `client.send_message`
    + Send a message to a specified room.
    + @param `roomID` String the room to send the message to
    + @param `body` String the text body to send. defaults to plain text
    + @param `textFormat` String OPTIONAL If the string is formatted. Must be "markdown" or "html"
    + @param `replyTo` String OPTIONAL The ID to the event you want to reply to
    + @param `isNotice` bool OPTIONAL Send the message as a notice. slightly grey on desktop.
    + @return dict contains 'event_id' of new message
    + Matrix supported HTML tags:
    + font, del, h1, h2, h3, h4, h5, h6, blockquote, p, a, ul, ol, sup, sub, 
    + li, b, i, u, strong, em, strike, code, hr, br, div, table, thead, tbody, 
    + tr, th, td, caption, pre, span, img.
    + an example markdown message would be `client.send_message(room.id, "this is __bold__ in a message", textFormat="markdown")`
+ `client.send_typing`
    + This typing notification will let the user know we've seen their message
    + @param `roomID` String the room id that you want to type in
    + @param `seconds` int OPTIONAL How many seconds you want to type for. Default 10
+ `client.change_presence`
    + This function is used to update your presence on the server. Status message support is client specific
    + @param `presence` enum/string OPTIONAL The presence of the bot user ie `halcyon.Presence.ONLINE` or `halcyon.Presence.UNAVAILABLE` if idle.
    + @param `statusMessage` String the string to set the current users status to
+ `client.send_image`
    + Send an image to a room
    + @param `roomID` String the room to send to
    + @param `fileBuffer` BytesIO The file in bytes format
    + @param `fileName` String the file name of the file
    + @param `generate_blurhash` Bool Generate a Blurhash for the image. This is a blur used as filler while the image loads. Defaults True
    + @param `generate_thumbnail` Bool Set to true to automatically downsize images over 640x640. Defaults True

## halcyon event handlers
+ `async def on_ready():`
    + This is called after login, right before we start handling messages. Good for telling you your bot is online, or to configure things  
+ `async def on_message(message):`
    + This is called for each message received, including messages with attachments
+ `async def on_message_edit(message):`
    + This is called when a message is edited
+ `async def on_room_invite(room):`
    + This is called when you are invited to a room
+ `async def on_room_leave(roomID):`
    + This is called when you leave a room (or are kicked)

## halcyon room object
Below are all of the current values stored in the room objects, inside an example usage of on_message(message). Non populated values default to none, or an empty list where required.
```python
@client.event
async def on_message(message):
    message.room.creator #userID of who made the room 
    message.room.version #room version
    message.room.federated #is this room allowed to federate to other servers?
    message.room.predecessor.room #the roomID before this (defaults None if there isnt one)
    message.room.predecessor.event #the event where the room updated
    message.room.joinRule #the joinrule for the room
    message.room.name #name of the room
    message.room.topic #room topic
    message.room.alias.canonical #main, canonical, address
    message.room.alias.alt #alternative addresses
    message.room.avatar.url #the mxc:// url of the avatar
    message.room.members #list, all the room members that have joined
    message.room.left #list, all of the users who have left
    message.room.invited #list, all of the users who have been invited but not joined

    message.room.permissions.administrators #a list of users who are considered administrators
    message.room.permissions.moderators #a list of users who are considered moderators
    message.room.permissions.users #all the users with non 0 power levels

    message.room.permissions.m_event_values #a dict() of m.events and the value required to send them
    message.room.permissions.administrator_value #the permission value for administrators (always 100)
    message.room.permissions.moderator_value #the permission value for administrators (always 50)
    message.room.permissions.user_value #the permission value for administrators (0)
    message.room.permissions.events_value #The level required to send specific event types
    message.room.permissions.state_value #The level required to send state events
    message.room.permissions.invite_value #The level required to invite a user
    message.room.permissions.redact_value #The level required to redact other users comments 
    message.room.permissions.ban_value #The level required to ban a user
    message.room.permissions.kick_value #The level required to kick a user

    message.room.relatedGroups #a list of related groups for this room (ie groups)
    message.room.guestAccess #T/F do we allow guest access?
    message.room.historyVisibility #["invited", "joined", "shared", "world_readable"] 
    message.room.acl #if any server ACL has been specified for this room
    message.room.encryption #information on the rooms encryption (if any)
```


## Halcyon configuration
+ `client.run(halcyonToken=None, userID=None, password=None, homeserver=None, longPollTimeout=None)`
    + You only need to pass in the `halcyonToken`. If you would like to use password login without a token, you need the us/pw/hs combo. 
    + `longPollTimeout` is time in seconds to long poll the server for more matrix messages. The higher the number, the nicer you are to the server. Editing this does not affect how long it takes for new matrix messages to reach your bot, but it does save network data the higher it is. Default is 10 seconds. Do note, while we wait for the server response, signals to the lib are queued (ie ability to use ctrl^c). After doing a ctrl^c, wait for the network timer to go up, or start typing a message in a channel the bot is in.


## Hot tip
+ You can use something like `message._raw` or `message.content._raw` to see the raw message json
+ Set `longPollTimeout=1` for debugging (but don't forget to change it back!)
