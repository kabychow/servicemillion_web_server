import asyncio
import websockets
from threading import Thread
from src import customer
from src.routes import app

Thread(target=app.run, args=('0.0.0.0',)).start()
asyncio.get_event_loop().run_until_complete(websockets.serve(customer.handle, port=8844))
# asyncio.get_event_loop().run_until_complete(websockets.serve(agent.handle, port=8845))
asyncio.get_event_loop().run_forever()
