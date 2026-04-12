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

## R2.5
- [x] Replace one-off `/sync` parsing with a generic event pipeline for `timeline`, `state`, `ephemeral`, `account_data`, `presence`, and `to_device`
- [x] Add a stable event dispatch design so new Matrix event types can be registered without rewriting the main loop
- [x] Keep room cache in sync from live state updates instead of relying mostly on periodic rebuilds
- [x] Expand room event coverage for useful bot cases first
- [x] `m.room.member` full lifecycle support: join, leave, invite, ban, knock, profile updates
- [x] `m.reaction` support
- [x] `m.room.redaction` support
- [x] `m.sticker` support
- [x] `m.room.pinned_events` support
- [x] `m.room.tombstone` support
- [x] Live handling for room state events we already model in the room object
- [x] Improve message relations support for replies, edits, references, annotations, and threads
- [x] Support useful non-room events that bots may want to observe
- [x] `m.typing` support
- [x] `m.receipt` support
- [x] `m.presence` receive support
- [x] Room account data support via `AccountDataEvent` through `on_event`
- [x] Global account data support via `AccountDataEvent` through `on_event`
- [x] Add a real user object instead of exposing only raw sender IDs
- [x] Add a common raw-event escape hatch so unsupported events are still inspectable by library users
- [x] Review and clean up the public hook API so it stays small, predictable, and easy to document
- [x] Add tests per event family instead of only per object parser
- [x] Expand docs around event coverage, guarantees, and unsupported behavior
- [x] Update old spec references to the current Matrix spec version instead of `r0.6.1`
- `on_message` now handles message-like timeline content, including `m.sticker`
- `on_event` should be treated as the fallback for all Matrix event objects present in `/sync`
- `room.left` now tracks actual `leave` membership only
- `room.banned` and `room.knocked` are now tracked separately

## R3
- [ ] serverside account data utils https://spec.matrix.org/latest/client-server-api/#put_matrixclientv3useruseridaccount_datatype
- [ ] generate secure curve
- [ ] upload public key
- [ ] m.dummy support
- [ ] room events https://spec.matrix.org/latest/client-server-api/#room-events
- [ ] /sync extension https://spec.matrix.org/latest/client-server-api/#syncing
- [ ] encryption
- [ ] read/write server datastore
- [ ] datastore key in token
- [ ] warn log when token doesn't cant support encryption
- [x] bot info (user id, device id, auth type, homeserver)
- [x] fix async issues that lock the bot while longpolling

## R4 / Future 
- [ ] post video messages
- [ ] post file messages
- [ ] post audio messages
- [x] user object
- [x] get user presence/status
- [x] get user image
- [x] get user nick
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
