import halcyon, json
import io
import requests

client = halcyon.Client()

"""
The following bot will 
    1. Join a room when invited
    2. Download and save any image it sees sent
    3. Sets its status to "Archiving images"
"""

@client.event
async def on_room_invite(room):
    print("Someone invited us to join " + room.name)
    await client.join_room(room.id)
    await client.send_message(room.id, body="Hello humans")


@client.event
async def on_message(message):
    print(message.event.id)
    
    #if the message is an image message, download it and save its name
    if (message.content.type == halcyon.msgType.IMAGE):
        print("Found an image!")

        #download the image and name
        image = await client.download_media(message.content.url)
        image_name = message.content.body

        #save the the image 
        with open("./archived_" + image_name, "wb") as f:
            f.write(image.getbuffer())

        await client.send_message(message.room.id, body="Image archived!", replyTo=message.event.id)


@client.event
async def on_ready():
    print("Online!")
    await client.change_presence(statusMessage="Archiving images")

if __name__ == '__main__':
    client.run(halcyonToken="eyJ0eX...")