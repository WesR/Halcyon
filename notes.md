# Notes, ideas, and goals
As of right now, you can login, then you get a long lived token

Room obj ideas: 
+ have a room full and room minimal, because you don't normally need to waste the time parsing all this
+ alternatively, have a room Cache state that gets build on botup

Handle:
Type: 
+ m.room.message [FULL]
+ m.reaction
+ m.room.member


## Outline

1. Base overide hooks from the main bot loop
2. Save keys fully on server, not locally
3. Only deal with new events

## MVP

- [x] Login
- [x] Login with un/pw
- [X] Fetch for new messages every x seconds using await
- [x] Have hook for text payload (on_message)
- [x] Can join rooms
- [x] simple user token
- [x] client.send_message
- [x] documentation
- [x] GitHub whl builder

## RC 2
- [x] Bot on_ready
- [ ] Room cache (dict of room obj to build off of)
- [x] Media REST services
- [x] Send and receive Media
- [ ] set presence/status
- [ ] get presence/status
- [x] send_typing
- [ ] better documentation

## RC 3
- [ ] leave room
- [ ] list rooms
- [ ] get room permissions
- [ ] ban user from room
- [ ] emotes

## RC 4
- [ ] encryption
- [ ] read/write server datastore
- [ ] datastore key in token
- [ ] warn log when token doesn't cant support encryption

## Goals

1. simple user token
2. on_message
3. on_ready
4. client.send_message
5. Encrypted messages
6. client presence
7. client.send_typing

This was a design idea, not actual code. I needed something to work to.
```python
client = halcyon.Client()

client.run('username.password.deviceID.accessToken') #All base64

@client.event
async def on_message(message):
    if (message.payload.content.text == 'hello'):
        await client.send_typing(message.payload.channel, message.is_encrypted)
        await client.send_message(message.payload.channel, message.is_encrypted, 'goodbye')
        #await client.send_message(message.payload.channel, message.not_encrypted, 'goodbye')
@client.event
async def on_ready():
    print("Online")
    await client.change_presence(presence=LerasiumOxide.status.online, status="Baking cookies")
```