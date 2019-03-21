import asyncio
import websockets
from handlers import client_handler, agent_handler

asyncio.get_event_loop().run_until_complete(websockets.serve(client_handler.handle, port=8844))
asyncio.get_event_loop().run_until_complete(websockets.serve(agent_handler.handle, port=8845))
asyncio.get_event_loop().run_forever()
