from starlette.responses import Response, JSONResponse, RedirectResponse
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from app.utilities import gen_token, authenticated
from app.constants import db

templates = Jinja2Templates(directory='templates')


async def main(request: Request) -> Response:
    return templates.TemplateResponse('home.html', {'request': request})


async def signup(request: Request) -> Response:
    token = gen_token()
    return templates.TemplateResponse('signup.html', {'request': request, 'token': token})


async def login(request: Request) -> Response:
    token = gen_token()
    return templates.TemplateResponse('login.html', {'request': request, 'token': token})


async def message(request: Request) -> Response:
    if not authenticated(request.cookies, request.cookies.get('email')):
        return RedirectResponse('/login')

    sender = request.cookies.get('email')
    mem_hash = int(request.query_params.get('hash'))
    members = db.conversations.find_one({'hash': mem_hash})['members']
    if sender not in members:
        return RedirectResponse('/login')
    return templates.TemplateResponse('message.html', {
        'request': request, 'token': gen_token(sender), 'sender': sender, 'members': members, 'hash': mem_hash
    })


async def conversation(request: Request) -> Response:
    if not authenticated(request.cookies, request.cookies.get('email')):
        return RedirectResponse('/login')
    return templates.TemplateResponse('conversation.html', {'request': request, 'sender': request.cookies.get('email')})
