import os
import asyncio
import random
import websockets
import json


async def handler(websocket, path):
    while True:
        data = {
            "symbol": random.randint(0, 1000),
            "price": random.randint(1001, 2000),
            "change": random.randint(2001, 3000),
        }
        await websocket.send(json.dumps(data))
        await asyncio.sleep(0.05)


start_server = websockets.serve(handler, "127.0.0.1", 8080)
os.system("start https://nevatia.github.io/nevatiastream.github.io/")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
