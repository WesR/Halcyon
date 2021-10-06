## Halcyon *on and on*

The goal of this project is to have an easy to install and use Matrix bot library similar to the Discord or Slack libs.
Encryption must be transparent to the user. Check the roadmap in [notes.md](./notes.md)

## Current features
- [x] A nice command prompt to generate Halcyon tokens
- [x] Login with token or username/password
- [X] Fetch for new messages every x seconds using await
- [x] Event hooks for
    - [x] on_message(self, message)
    - [x] on_message_edit(self, message)
    - [x] on_room_invite(self, room)
    - [x] on_room_leave(self, roomID)
- [x] Action hooks
    - [x] send_message(self, roomID, body, textFormat=None, replyTo=None, isNotice=False)
    - [x] async def join_room(self, roomID)
- [ ] documentation
- [ ] github whl builder

## Getting started
1. Create an account to use as a bot account
2. Install using `python3 -m pip install halcyon-matrix` or using the Releases tab
3. Generate a token using `python3 -m halcyon -s homeserver.xyz -u @user:homeserver.xyz -p yourP@$$w0rd`
4. Start with the demo below

## Example bot code

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
    if "give me random" in message.content.body:
        body = "This looks random: " + requests.get("https://random.wesring.com").json()["value"]
        await client.send_message(message.room.id, body=body, replyTo=message.event.id)


if __name__ == '__main__':
    client.run(halcyonToken="eyJ0eXAiO...")
```

### CLI usage
halcyon can be called from the CLI to do some managment of the account. See the readme with `python3 -m halcyon -h`

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
