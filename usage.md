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

## Example text bot
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
        body = "This looks random: " + requests.get("https://random.wesring.com").json()["value"]
        await client.send_message(message.room.id, body=body, replyTo=message.event.id)


@client.event
async def on_ready():
    print("Online!")

if __name__ == '__main__':
    client.run(halcyonToken="eyJ0eXAiO...")
```

## Example file bot
This bot will auto join invited rooms. If it sees a message of type image, it will download the image into the lastImage var. When it sees the text "dump last file", it will upload the file to your homeserver under a new mxc URL, and send a message with that mxc url.

The following are the recognized message types:
+ TEXT
+ EMOTE
+ NOTICE
+ IMAGE
+ FILE
+ AUDIO
+ LOCATION
+ VIDEO


Note: The file API is subject to change, and is currently under development. 
```python
import halcyon, json
import requests

client = halcyon.Client(ignoreFirstSync=True)

lastImage = None
lastImageName = ''

@client.event
async def on_room_invite(room):
    print("Someone invited us to join " + room.name)
    await client.join_room(room.id)
    await client.send_message(room.id, body="Hello humans")


@client.event
async def on_message(message):
    global lastImage
    global lastImageName

    print(message.event.id)
    if (message.type == halcyon.msgType.IMAGE):
        lastImage = await client.download_media(message.content.url)
        lastImageName = message.content.body
        return

    if "dump last file" in message.content.body:
        resp = await client.upload_media(lastImage, lastImageName)
        await client.send_message(message.room.id, body="the new mxc is " + resp["content_uri"])

if __name__ == '__main__':
    client.run(halcyonToken="eyJ0eX...")
```

## halcyon function documentation
+ client.send_message
  + Send a message to a specified room.
  + @param roomID String the room to send the message to
  + @param body String the text body to send. defaults to plain text
  + @param textFormat String OPTIONAL If the string is formatted. Must be "markdown" or "html"
  + @param replyTo String OPTIONAL The ID to the event you want to reply to
  + @param isNotice bool OPTIONAL Send the message as a notice. slightly grey on desktop.
  + @return dict contains 'event_id' of new message
  + Matrix supported HTML tags:
  + font, del, h1, h2, h3, h4, h5, h6, blockquote, p, a, ul, ol, sup, sub, 
  + li, b, i, u, strong, em, strike, code, hr, br, div, table, thead, tbody, 
  + tr, th, td, caption, pre, span, img.
  + an example markdown message would be `client.send_message(room.id, "this is __bold__ in a message", textFormat="markdown")`


## halcyon event handlers
+ async def on_ready():
  + This is called after login, right before we start handling messages. Good for telling you your bot is online, or to configure things  
+ async def on_message(message):
  + This is called for each message received, including messages with attachments
+ async def on_message_edit(message):
  + This is called when a message is edited
+ async def on_room_invite(room):
  + This is called when you are invited to a room
+ async def on_room_leave(roomID):
  + This is called when you leave a room (or are kicked)

## Hot tip

you can use something like `message._raw` or `message.content._raw` to see the raw message json
