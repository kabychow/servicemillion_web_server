import asyncio
import websockets
from threading import Thread
from src.chat import handle_agent, handle_customer
from src.routes import app
import warnings
warnings.filterwarnings('ignore')

Thread(target=app.run, args=('0.0.0.0',)).start()
asyncio.get_event_loop().run_until_complete(websockets.serve(handle_customer, port=8844, max_size=2**24))
asyncio.get_event_loop().run_until_complete(websockets.serve(handle_agent, port=8845, max_size=2**24))
asyncio.get_event_loop().run_forever()
