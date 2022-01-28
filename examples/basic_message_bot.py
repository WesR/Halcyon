import halcyon, json

import requests

"""
    This is a basic message bot that will

    1. Join a room that it is invited to
    2. Reply to any user who says the magic phrase "give me random" with a random string of characters
    2. Sets an online status when the bot is online
"""


client = halcyon.Client()

@client.event
async def on_room_invite(room):
    print("Someone invited us to join " + room.name)
    await client.join_room(room.id)
    await client.send_message(room.id, body="Hello humans")


@client.event
async def on_message(message):
    print(message.event.id)#This is the event id for the message we just recived

    if "give me random" in message.content.body:
        await client.send_typing(message.room.id)
        body = "This looks random: " + requests.get("https://random.wesring.com").json()["value"]
        await client.send_message(message.room.id, body=body, replyTo=message.event.id)

@client.event
async def on_ready():
    print("Online!")
    await client.change_presence(statusMessage="indexing /dev/urandom")

if __name__ == '__main__':
    #The halcyon token is generated from the CLI tool. Check out usage.md in the repo for more info

    client.run(halcyonToken="eyJ0eXAiO...", longPollTimeout=30)
    #you can lower the long poll when testing, but its nicer to the server to leave it longer
    #it does not effect performance, just how long it takes to kill the bot when you use ctrl^c