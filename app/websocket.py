from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.responses import JSONResponse, Response
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
import urllib.parse
from app.utilities import authenticated, verify_session_utility, get_messages
from app.constants import motor


class WebSocketManager:
    def __init__(self):
        self.connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, mem_hash: int) -> None:
        print(f'connecting with {mem_hash}')
        await websocket.accept(headers=[(b'connection', b'keep-alive')])
        # Check if conversation hash is already open in connections
        if mem_hash in self.connections:
            # If it is, check if this particular websocket is already registered
            if websocket in self.connections[mem_hash]:
                # If it is, exit
                return
            else:
                # If not, add this websocket to self.connections under the conversation hash
                self.connections[mem_hash].append(websocket)
        else:
            # If not, create new entry in connections with conversation hash and websocket
            self.connections[mem_hash] = [websocket]
        print(self.connections)

    def disconnect(self, websocket: WebSocket, mem_hash: int) -> None:
        if mem_hash in self.connections:
            if websocket in self.connections[mem_hash]:
                self.connections[mem_hash].remove(websocket)
                if len(self.connections[mem_hash]) == 0:
                    self.connections.pop(mem_hash)
        if mem_hash in watching:
            watching.remove(mem_hash)

    async def update(self, data: dict | list | str, mem_hash: int) -> None:
        print(f'Updating {data}')
        print(f'This is mem hash: {mem_hash}')
        print(self.connections)
        if mem_hash in self.connections:
            websockets_to_remove = []
            for websocket in self.connections[mem_hash]:
                try:
                    print(data)
                    await websocket.send_json(data)
                except ConnectionClosedOK:
                    print('connection closed with ConnectionClosedOK')
                    websockets_to_remove.append(websocket)
                    continue
                except ConnectionClosedError:
                    print('connection closed with ConnectionClosedError')
                    websockets_to_remove.append(websocket)
                    continue
                except RuntimeError as e:
                    print('runtime error')
                    print(e)
                    websockets_to_remove.append(websocket)
                    continue
            print(websockets_to_remove)
            for websocket in websockets_to_remove:
                try:
                    self.connections[mem_hash].remove(websocket)
                    if len(self.connections[mem_hash]) == 0:
                        self.connections.pop(mem_hash)
                except (KeyError, ValueError) as e:
                    print(e)




manager = WebSocketManager()
watching = []


async def watch(websocket: WebSocket, mem_hash: int) -> None:
    while websocket in manager.connections[mem_hash]:
        async with motor.messages.watch(full_document='updateLookup') as change_stream:
            d = await change_stream.next()
            if 'fullDocument' not in d:
                continue
            message = d['fullDocument']


async def initialize(data: dict | list | str, websocket: WebSocket) -> None:
    try:
        await websocket.send_json(data)
    except ConnectionClosedOK:
        print('connection closed with ConnectionClosedOK')
    except ConnectionClosedError:
        print('connection closed with ConnectionClosedError')
    except RuntimeError as e:
        print('runtime error')
        print(e)


async def database_ws(websocket: WebSocket) -> JSONResponse | None:
    members = urllib.parse.unquote(websocket.query_params.get('members')).split(',')
    sender = urllib.parse.unquote(websocket.query_params.get('sender'))
    print(members)
    mem_hash = int(urllib.parse.unquote(websocket.query_params.get('hash')))
    if websocket.query_params.get('session_id'):
        session_id = urllib.parse.unquote(websocket.query_params.get('session_id'))
        if not verify_session_utility(session_id, sender):
            return JSONResponse({'error': 'Forbidden'}, 403)
    elif not authenticated(websocket.cookies, sender):
        return JSONResponse({'error': 'Forbidden'}, 403)

    await manager.connect(websocket, mem_hash)
    await initialize((get_messages(mem_hash, 20)), websocket)
    if mem_hash not in watching:
        watching.append(mem_hash)
        await watch(websocket, mem_hash)
    try:
        while True:
            await websocket.receive_text()
    except (ConnectionClosedError, WebSocketDisconnect) as e:
        print('error :((')
        print(e)
        print(type(e))
        print('closing websocket')
        manager.disconnect(websocket, mem_hash)
