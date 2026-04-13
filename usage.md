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
import aiohttp

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
    if "give me random" in message.text:
        await client.send_typing(message.room.id) # This typing notification will let the user know we've seen their message
        # Use async HTTP client for external requests (non-blocking)
        async with aiohttp.ClientSession() as session:
            async with session.get("https://random.wesring.com") as resp:
                data = await resp.json()
                body = f"This looks random: {data['value']}"
        await client.send_message(message.room.id, body=body, replyTo=message.event.id)


@client.event
async def on_ready():
    print("Online!")
    await client.change_presence(statusMessage="indexing /dev/urandom")

if __name__ == '__main__':
    client.run(halcyonToken="eyJ0eXAiO...")
```

**Pro tip:** Use `aiohttp.ClientSession()` instead of `requests` for external HTTP calls to avoid blocking the bot's event loop.

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
+ `client.get_user_presence`
    + Get a user's current presence/status information.
    + @param `userID` String OPTIONAL full Matrix user ID. Defaults to the logged in bot user.
    + @return `PresenceEvent` with `presence`, `status_msg`, `currently_active`, `last_active_ago`
    + If the homeserver returns an error, the raw error dict is returned instead.
    + example:
    ```python
    presence = await client.get_user_presence("@alice:example.org")
    print(presence.presence)      # "online" / "offline" / "unavailable"
    print(presence.status_msg)    # optional status message
    ```
+ `client.get_user_profile`
    + Get a user's profile information.
    + @param `userID` String full Matrix user ID
    + @return `User` with `id`, `displayname`, `avatar_url`
    + If the homeserver returns an error, the raw error dict is returned instead.
    + example:
    ```python
    profile = await client.get_user_profile("@alice:example.org")
    print(profile.displayname)
    print(profile.avatar_url)
    ```
+ `client.get_bot_info`
    + Get comprehensive bot information
    + @return Dict containing user_id, device_id, auth_type, and homeserver

## halcyon event handlers

Halcyon provides typed hooks for common events and a generic fallback for everything else. Typed hooks fire first, then `on_event` fires for the same event. Register hooks using the `@client.event` decorator.

+ `async def on_ready():`
    + Called after login, right before we start handling messages.
+ `async def on_message(message):`
    + Called for message-like timeline content. Right now this includes `m.room.message` and `m.sticker`. Receives a unified `message` object with developer-friendly helpers like `message.author`, `message.text`, `message.sticker`, and `message.attachments`.
+ `async def on_message_edit(message):`
    + Called when a message is edited (has `m.relates_to` with `rel_type: m.replace`).
+ `async def on_reaction(event):`
    + Called for `m.reaction` events. Receives a `ReactionEvent` with `reaction_key` and `relates_to_event_id`.
+ `async def on_redaction(event):`
    + Called for `m.room.redaction` events. Receives a `RedactionEvent` with `redacts` (target event ID) and optional `reason`.
+ `async def on_room_member(event):`
    + Called for `m.room.member` state changes (join, leave, ban, invite, knock). Receives a `MemberEvent`.
+ `async def on_room_invite(room):`
    + Called when you are invited to a room. Receives a `room` object built from invite stripped state.
+ `async def on_room_leave(roomID):`
    + Called when you leave a room (or are kicked). Receives the room ID string.
+ `async def on_event(event):`
    + fires for every Matrix event object present in `/sync`, including events handled by typed hooks above. Receives an `Event` (or typed subclass for stickers, presence, typing, receipts, account data, and other supported families). Use this to observe event types that don't have a dedicated hook.

### Dispatch order
1. Room state events update the room cache **before** any hook fires.
2. Typed hooks (`on_message`, `on_reaction`, etc.) fire for matching events.
3. `on_event` fires for the same event afterward.

### Event support matrix

| Event type | Typed wrapper | Hook | Source |
|---|---|---|---|
| `m.room.message` | `message` | `on_message` / `on_message_edit` | timeline |
| `m.reaction` | `ReactionEvent` | `on_reaction` | timeline |
| `m.room.redaction` | `RedactionEvent` | `on_redaction` | timeline |
| `m.room.member` | `MemberEvent` | `on_room_member` | timeline, state |
| `m.sticker` | `message` + `StickerEvent` | `on_message` + `on_event` | timeline |
| `m.typing` | `TypingEvent` | `on_event` | ephemeral |
| `m.receipt` | `ReceiptEvent` | `on_event` | ephemeral |
| `m.presence` | `PresenceEvent` | `on_event` | presence |
| invite/knock stripped state | `Event` | `on_event` | invite_state, knock_state |
| leave room event objects | `Event` / `AccountDataEvent` | `on_event` | leave_state, leave_timeline, leave_account_data |
| account data | `AccountDataEvent` | `on_event` | account_data |
| all other types | `Event` | `on_event` | varies |

Event objects delivered to `on_event` expose `.sender_user` (a `User` with `id`, `displayname`, `avatar_url`) when sender info is available in the room cache. The `message` object delivered to `on_message` exposes `message.author` for the same purpose.

## halcyon room object
Below are all of the current values stored in the room objects, inside an example usage of on_message(message). The room cache is updated live from sync state events. Non populated values default to `None`, `""`, or an empty list depending on the field.
```python
@client.event
async def on_message(message):
    # Core Room Information
    message.room.id #room ID
    
    # m.room.create (Complete Matrix v1.16+ support)
    message.room.creator #userID of who made the room 
    message.room.version #room version
    message.room.federated #is this room allowed to federate to other servers?
    message.room.room_type #room type (e.g., "m.space" for spaces)
    message.room.additional_creators #list of additional room creators (Matrix v1.16+)
    message.room.predecessor.room #the roomID before this (defaults None if there isnt one)
    message.room.predecessor.event #the event where the room updated
    
    # m.room.join_rules (Complete with restricted room support)
    message.room.joinRule #the joinrule for the room
    message.room.join_rule_allow #allow conditions for restricted rooms (Matrix v1.2+)
    
    # m.room.name
    message.room.name #name of the room
    
    # m.room.topic (Complete with MIME type support)
    message.room.topic #room topic
    message.room.topic_content #m.topic content object for MIME types (Matrix v1.15+)
    
    # m.room.canonical_alias
    message.room.alias.canonical #main, canonical, address
    message.room.alias.alt #alternative addresses
    
    # m.room.avatar (Complete with detailed metadata)
    message.room.avatar.url #the mxc:// url of the avatar
    message.room.avatar.info_height #avatar height in pixels
    message.room.avatar.info_width #avatar width in pixels
    message.room.avatar.info_mimetype #avatar MIME type
    message.room.avatar.info_size #avatar size in bytes
    message.room.avatar.info_thumbnail_url #avatar thumbnail URL
    message.room.avatar.info_thumbnail_info #avatar thumbnail metadata
    
    # m.room.member (Complete with user profiles and authorization)
    message.room.members #list, all the room members that have joined
    message.room.left #list, all of the users who have left
    message.room.invited #list, all of the users who have been invited but not joined
    message.room.banned #list, all of the users who are currently banned
    message.room.knocked #list, all of the users who have knocked but not joined
    
    # Detailed member information (New comprehensive support)
    member = message.room.member_details["@user:matrix.org"]  # Get detailed member info
    member.user_id #user ID
    member.membership #join, leave, invite, ban, knock
    member.avatar_url #member's avatar URL
    member.displayname #member's display name
    member.is_direct #whether this is a direct message room
    member.join_authorised_via_users_server #authorization server for restricted rooms
    member.reason #reason for membership change (kick/ban reasons)
    member.third_party_invite #third-party invite information
    
    # m.room.power_levels (Complete with notifications support)
    message.room.permissions.administrators #a dict of users who are considered administrators
    message.room.permissions.moderators #a dict of users who are considered moderators
    message.room.permissions.users #all the users with their power levels
    
    message.room.permissions.m_event_values #a dict() of m.events and the value required to send them
    message.room.permissions.administrator_value #the permission value for administrators (always 100)
    message.room.permissions.moderator_value #the permission value for moderators (always 50)
    message.room.permissions.user_value #the default permission value for users
    message.room.permissions.events_value #The level required to send specific event types
    message.room.permissions.state_value #The level required to send state events
    message.room.permissions.invite_value #The level required to invite a user
    message.room.permissions.redact_value #The level required to redact other users comments 
    message.room.permissions.ban_value #The level required to ban a user
    message.room.permissions.kick_value #The level required to kick a user
    message.room.permissions.notifications #notification power level settings
    
    # m.room.related_groups (Legacy support)
    message.room.relatedGroups #a list of related groups for this room (deprecated)
    
    # m.room.guest_access
    message.room.guestAccess #T/F do we allow guest access?
    
    # m.room.history_visibility
    message.room.historyVisibility #["invited", "joined", "shared", "world_readable"] 
    
    # m.room.server_acl (Complete with IP literal controls)
    message.room.acl.allow_ip_literals #whether IP literals are allowed
    message.room.acl.allow #list of allowed server patterns
    message.room.acl.deny #list of denied server patterns
    
    # m.room.encryption (Complete with rotation settings)
    message.room.encryption.algorithm #encryption algorithm used
    message.room.encryption.rotation_period_ms #key rotation period in milliseconds
    message.room.encryption.rotation_period_msgs #key rotation period in message count

    # m.room.pinned_events
    message.room.pinned_events #list of pinned event IDs

    # m.room.tombstone
    message.room.tombstone_body #human-readable reason the room was replaced
    message.room.tombstone_replacement_room #room ID of the replacement room

    # Message-like helpers
    message.id #event ID
    message.author.id #sender user ID
    message.author.displayname #sender display name when known
    message.author.avatar_url #sender avatar when known
    message.type # "m.room.message" or "m.sticker"
    message.text #text body for text/notice/emote messages, else ""
    message.sticker #Sticker object for sticker events, else None
    message.attachments #list of Attachment objects for image/file/audio/video messages
    message.body #normalized body/helper for message-like events, defaults ""
    message.url #normalized MXC URL/helper for sticker and attachment messages
    message.info #normalized FileInfo/helper for sticker and attachment messages
    message.is_sticker #True for sticker timeline events

    # Sticker helper object
    if message.sticker:
        message.sticker.body
        message.sticker.url
        message.sticker.info
        message.sticker.width
        message.sticker.height
        message.sticker.mimetype
        message.sticker.thumbnail_url

    # Attachment helper objects
    if message.attachments:
        attachment = message.attachments[0]
        attachment.type
        attachment.body
        attachment.url
        attachment.filename
        attachment.info
        attachment.width
        attachment.height
        attachment.mimetype
        attachment.duration
        attachment.thumbnail_url
```


## Halcyon configuration
+ `client.run(halcyonToken=None, userID=None, password=None, homeserver=None, longPollTimeout=None)`
    + You only need to pass in the `halcyonToken`. If you would like to use password login without a token, you need the us/pw/hs combo. 
    + `longPollTimeout` is time in seconds to long poll the server for more matrix messages. The higher the number, the nicer you are to the server. Editing this does not affect how long it takes for new matrix messages to reach your bot, but it does save network calls. Default is 10 seconds.


## Hot tip
+ You can use something like `message._raw` or `message.content._raw` to see the raw message json
+ Set `longPollTimeout=1` for debugging (but don't forget to change it back!)
