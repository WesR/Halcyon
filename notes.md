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

room cache
1. on boot fetch list of rooms
2. Check full room events
3. save cache in halcyon so we can add the info to every message
4. function to read from cache
5. function to build cache for room
6. cache for joined users
struct:
{
    cache-init-age: datetime()
    rooms: {
        id : {cache},
        id : {cache}
    }
}



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

## R2
- [x] Bot on_ready
- [x] Room cache (dict of room obj to build off of)
- [x] get room permissions
- [x] get room info
- [x] Media REST services
- [x] Send and receive Media
- [x] set presence/status
- [x] send_typing
- [x] better documentation
- [x] Improve /sync calls
- [x] roomcache update intervals
- [x] post image messages

## R3
- [ ] serverside account data utils https://matrix.org/docs/spec/client_server/r0.6.1#put-matrix-client-r0-user-userid-account-data-type
- [ ] generate secure curve
- [ ] upload public key
- [ ] m.dummy support
- [ ] room events https://matrix.org/docs/spec/client_server/r0.6.1#id459
- [ ] /sync extension https://matrix.org/docs/spec/client_server/r0.6.1#id84
- [ ] encryption
- [ ] read/write server datastore
- [ ] datastore key in token
- [ ] warn log when token doesn't cant support encryption
- [x] bot info (user id, client token, auth type)
- [x] fix async issues that lock the bot while longpolling

## R4 / Future 
- [ ] post video messages
- [ ] post file messages
- [ ] post audio messages
- [ ] user object
- [ ] get user presence/status
- [ ] get user image
- [ ] get user nick
- [ ] search for user
- [ ] leave room
- [ ] list rooms
- [ ] ban user from room
- [ ] emotes

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