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
2. Install the package with `python3 -m pip install halcyon`
3. Generate a token using `python3 -m halcyon.py -s homeserver.xyz -u @user:homeserver.xyz -p yourP@$$w0rd`
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