import halcyon
import aiohttp
import asyncio
import json

"""
    This is an async-friendly message bot that demonstrates best practices:

    1. Uses async context managers for proper resource cleanup
    2. Uses aiohttp for external HTTP calls (non-blocking)
    3. Shows proper async/await patterns
    4. Demonstrates concurrent operations
"""

# Create client instance
client = halcyon.Client()

@client.event
async def on_room_invite(room):
    print(f"Someone invited us to join {room.name}")
    await client.join_room(room.id)
    await client.send_message(room.id, body="Hello humans! I'm running with proper async support")

@client.event
async def on_message(message):
    print(f"Received message: {message.event.id}")
    # Show typing indicator while we work
    await client.send_typing(message.room.id)

    if "give me random" in message.content.body:
        # Use async HTTP client for external requests (non-blocking)
        async with aiohttp.ClientSession() as session:
            async with session.get("https://random.wesring.com") as resp:
                if resp.status == 200:
                    data = json.loads(await resp.text())
                    body = f"This looks random: {data['value']}"
                else:
                    body = "Failed to get random data"
        
        # Send response
        await client.send_message(message.room.id, body=body, replyTo=message.event.id)
    
    elif "give me concurrent random" in message.content.body:
        # Start multiple async operations concurrently
        async def fetch_url(session, url, name):
            async with session.get(url) as resp:
                data = json.loads(await resp.text())
                return f"{name}: {data['value']}"
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                fetch_url(session, "https://random.wesring.com", 'random 1'),
                fetch_url(session, "https://random.wesring.com", 'random 2'),  
                fetch_url(session, "https://random.wesring.com", 'random 3')
            ]
            
            # Wait for all requests to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            response = "Concurrent requests completed:\n" + "\n".join(str(r) for r in results)
            await client.send_message(message.room.id, body=response, replyTo=message.event.id)

@client.event
async def on_ready():
    print("Bot is online")
    await client.change_presence(statusMessage="Running with async")

if __name__ == '__main__':
    client.run(halcyonToken="eyJ0eXAiO...", longPollTimeout=30)
    
    # Alternative: Use async context manager for automatic cleanup
    # async def main():
    #     async with halcyon.Client() as client:
    #         # Set up event handlers here
    #         await client.run_async(halcyonToken="eyJ0eXAiO...")
    # 
    # asyncio.run(main())