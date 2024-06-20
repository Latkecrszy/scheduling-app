from starlette.applications import Starlette
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.staticfiles import StaticFiles
from app.endpoints import *
from app.templates import *
from app.websocket import database_ws


routes = [
    WebSocketRoute('/database_ws', endpoint=database_ws),
    Route('/', endpoint=main, methods=['GET']),
    Route('/login', endpoint=login, methods=['GET']),
    Route('/signup', endpoint=signup, methods=['GET']),
    Route('/message', endpoint=message, methods=['GET']),
    Route('/create-account', endpoint=create_account, methods=['POST']),
    Route('/sign_in', endpoint=sign_in, methods=['POST']),
    Route('/set_cookie', endpoint=set_cookie, methods=['GET']),
    Route('/verify-session', endpoint=verify_session, methods=['GET']),
    Route('/logout', endpoint=logout, methods=['GET']),
    Route('/delete_account', endpoint=delete_account, methods=['POST']),
    Route('/change-password', endpoint=change_password, methods=['POST']),
    Route('/send-message', endpoint=send_message, methods=['POST']),
    Route('/conversation', endpoint=conversation, methods=['GET']),
    Route('/create-conversation', endpoint=create_conversation, methods=['POST']),
    Route('/get-messages', endpoint=get_messages_endpoint, methods=['GET']),
    Mount('/static', StaticFiles(directory='static'), name='globals.css'),
    Mount('/static', StaticFiles(directory='static'), name='login.css'),
    Mount('/static', StaticFiles(directory='static'), name='home.css'),
    Mount('/static', StaticFiles(directory='static'), name='messages.css'),
]


app = Starlette(debug=True, routes=routes)
