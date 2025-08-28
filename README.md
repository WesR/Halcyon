## Halcyon

Halcyon is a Matrix bot library with the goal of being easy to install and use. The library takes inspiration from discord.py and the Slack libraries.
Encryption is on the roadmap, and with the goal of being transparent to the user. Check the roadmap in [notes.md](./notes.md), and see information of the token format in [tokenFormat.md](./tokenFormat.md)

Ask questions in the matrix chat [#halcyon:blackline.xyz](https://matrix.to/#/#halcyon:blackline.xyz) or in GitHub issues.

## Current features
- A nice CLI tool to generate Halcyon tokens
- Login with token or username/password
- Async long polling for new messages with non-blocking event loop
- Event hooks for
    - on_ready()
    - on_message(message)
    - on_message_edit(message)
    - on_room_invite(room)
    - on_room_leave(roomID)
- Action hooks
    - send_message(roomID, body, textFormat, replyTo, isNotice)
    - send_typing(roomID, seconds)
    - change_presence(presence, statusMessage)
    - join_room(roomID)
    - download_media(mxc)
    - upload_media(fileBuffer, fileName)
    - send_image(roomID, fileBuffer, fileName, generate_blurhash, generate_thumbnail)
- Room and message objects for incoming events events
- Basic documentation (Check [usage.md](./usage.md))

## Getting started
1. Create a matrix account for the bot
2. Install Halcyon using `python3 -m pip install halcyon` or download it from the Releases tab in Github
3. Generate a token using `python3 -m halcyon -s homeserver.xyz -u @user:homeserver.xyz -p yourP@$$w0rd`
4. Start with the demo code below

## Example bot code
See more example and message object info in [usage.md](./usage.md)
+ [Example async message bot](./examples/async_message_bot.py), looks for a phrase and replies with a phrase or async called responses
+ [Example message bot](./examples/basic_message_bot.py), looks for a phrase and replies with a phrase
+ [Example image bot](./examples/basic_image_bot.py), looks for a phrase and replies with an image
+ [Image Archive bot](./examples/image_archive_bot.py), looks for images, and saves them
```python
import halcyon
import aiohttp, json

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
        # Use async HTTP client for external requests (non-blocking)
        async with aiohttp.ClientSession() as session:
            async with session.get("https://random.wesring.com") as resp:
                data = json.loads(await resp.text())
                body = f"This looks random: {data['value']}"
        await client.send_message(message.room.id, body=body, replyTo=message.event.id)


@client.event
async def on_ready():
    print("Online!")
    await client.change_presence(statusMessage="indexing /dev/urandom")

if __name__ == '__main__':
    client.run(halcyonToken="eyJ0eXAiO...")
```

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
