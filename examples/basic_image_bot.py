import halcyon, json
import requests

client = halcyon.Client(ignoreFirstSync=True)

"""
    This is a basic that will
    1. Join a room that it is invited to
    2. Reply to any user who says the magic phrase "give me art" with randomly generated artwork from thisartworkdoesnotexist.com
    2. Sets an online status when the bot is online
"""


@client.event
async def on_room_invite(room):
    print("Someone invited us to join " + room.name)
    await client.join_room(room.id)
    await client.send_message(room.id, body="Hello humans")


@client.event
async def on_message(message):
    print(message.event.id)

    if "give me art" in message.content.body:
        await client.send_typing(message.room.id)
        resp = requests.get("http://thisartworkdoesnotexist.com/")#Please don't abuse them!
        await client.send_image(message.room.id, resp.content, "art.jpeg")

        """
        The example below sends an image as received, disabling features at the gain of no local image processing
        Note: generate_thumbnail will only downsize images if they are over 640x640px
        await client.send_image(message.room.id, resp.content, "art.jpeg", generate_blurhash=False, generate_thumbnail=False)
        """

@client.event
async def on_ready():
    print("Online!")
    await client.change_presence(statusMessage="testing code...")

if __name__ == '__main__':
    #The halcyon token is generated from the CLI tool. Check out usage.md in the repo for more info

    client.run(halcyonToken="eyJ0eXAiO...", longPollTimeout=10)
    #you can lower the long poll when testing, but its nicer to the server to leave it longer
    #it does not effect performance, just how long it takes to kill the bot when you use ctrl^c