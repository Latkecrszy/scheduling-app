from app.constants import db, ph, motor
from app.utilities import *
from starlette.responses import Response, JSONResponse, RedirectResponse
from starlette.requests import Request
import re, time
from argon2 import exceptions
from app.websocket import manager


async def create_account(request: Request) -> Response:
    data = await request.json()
    email = data.get('email').lower()
    if not db.anonymous_tokens.find_one({'token': data.get('token')}):
        return JSONResponse({'error': 'Invalid token', 'code': 403, 'token': gen_token()}, 403)
    elif db.accounts.find_one({'email': email}) is not None:
        return JSONResponse({'error': 'Account already exists', 'code': 403, 'token': gen_token()}, 403)
    elif not re.search('^[^@ ]+@[^@ ]+\.[^@ .]{2,}$', email):
        return JSONResponse({'error': 'Invalid email', 'code': 403, 'token': gen_token()}, 403)
    elif data.get('password') or data.get('password') == '':
        if len(data.get('password')) < 8:
            return JSONResponse({'error': 'Password must be at least 8 characters', 'code': 403}, 403)

    account = {
        'email': email,
    }

    if data.get('password'):
        account['password'] = ph.hash(data.get('password'))

    db.accounts.insert_one(account)

    return JSONResponse({'error': '', 'token': gen_token(email)})


async def sign_in(request: Request) -> Response:
    data = await request.json()
    email = data.get('email').lower()
    if not db.anonymous_tokens.find_one({'token': data.get('token')}):
        return JSONResponse({'error': 'Invalid token', 'code': 403, 'token': gen_token()}, 403)
    try:
        ph.verify(db.accounts.find_one({'email': email})['password'], data.get('password'))
    except exceptions.VerifyMismatchError:
        return JSONResponse({'error': 'Incorrect password', 'code': 403, 'token': gen_token()}, 403)
    except TypeError:
        return JSONResponse({'error': 'Account not found', 'code': 403, 'token': gen_token()}, 403)

    return JSONResponse({'error': '', 'token': gen_token(email)})


async def set_cookie(request: Request) -> Response:
    email = request.query_params.get('email').lower()
    print(request.url)
    if not db.tokens.find_one({'token': request.query_params.get('token'), 'email': email}):
        return RedirectResponse(f'/{request.url}?error=invalid_token', 303)
    elif db.accounts.find_one({'email': email}) is None:
        return RedirectResponse(f'/{request.url}?error=account_not_found', 303)

    response = RedirectResponse('/')
    response.set_cookie('email', email)
    response.set_cookie('session_id', gen_session(email), max_age=3153600000)
    print(request.url)

    db.tokens.find_one_and_delete({'token': request.query_params.get('token')})
    return response


async def verify_session(request: Request) -> Response:
    if not authenticated(request.cookies, request.headers.get('email')):
        return JSONResponse({'error': 'Forbidden', 'code': 403}, 403)
    return JSONResponse(verify_session_utility(request.headers.get('session_id'), request.headers.get('email')))


async def logout(request: Request) -> Response:
    if not authenticated(request.cookies, request.headers.get('email')):
        return JSONResponse({'error': 'Forbidden', 'code': 403}, 403)
    db.sessions.find_one_and_delete({'session_id': request.headers.get('session_id')})
    return JSONResponse({'error': ''}, 200)


async def delete_account(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email')):
        return JSONResponse({'error': 'Forbidden', 'code': 403}, 403)
    db.accounts.find_one_and_delete({'email': data.get('email')})
    db.sessions.find_one_and_delete({'email': data.get('email')})
    return JSONResponse({'error': ''}, 200)


async def change_password(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email')):
        return JSONResponse({'error': 'Forbidden', 'code': 403}, 403)
    try:
        ph.verify(db.accounts.find_one({'email': data.get('email')})['password'], data.get('old_password'))
    except exceptions.VerifyMismatchError:
        return JSONResponse({'error': 'Incorrect password', 'code': 403}, 403)
    except TypeError:
        return JSONResponse({'error': 'Account not found', 'code': 403}, 403)

    db.accounts.find_one_and_update({'email': data.get('email')}, {'$set': {'password': ph.hash(data.get('new_password'))}})
    return JSONResponse({'error': ''}, 200)


async def send_message(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('sender')) or not verify_token(data.get('token'), data.get('sender')):
        return JSONResponse({'error': 'Forbidden', 'code': 403}, 403)
    members = data.get('members')
    mem_hash = int(data.get('hash'))
    conversation = await motor.conversations.find_one({'hash': mem_hash})
    if conversation is None:
        return JSONResponse({'error': 'Conversation not found', 'code': 404}, 404)
    await motor.messages.insert_one({'hash': mem_hash, 'sender': data.get('sender'), 'members': data.get('members'),
        'text': data.get('text'), 'date': time.time(), 'id': gen_msg_id(), 'type': 'text'})
    await manager.update(get_messages(hash_list(members), 1), mem_hash)
    print(get_messages(mem_hash))
    return JSONResponse({'error': ''}, 200)


async def edit_message(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('sender')) or not verify_token(data.get('token'), data.get('sender')):
        return JSONResponse({'error': 'Forbidden', 'code': 403}, 403)
    msg_id = int(data.get('id'))
    mem_hash = int(data.get('hash'))
    await motor.messages.find_one_and_update({'id': msg_id}, {'text': data.get('text')})
    await manager.update(get_message(msg_id), mem_hash)
    return JSONResponse({'error': ''}, 200)


async def delete_message(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('sender')) or not verify_token(data.get('token'), data.get('sender')):
        return JSONResponse({'error': 'Forbidden', 'code': 403}, 403)
    msg_id = int(data.get('id'))
    mem_hash = int(data.get('hash'))
    await motor.messages.find_one_and_delete({'id': msg_id})
    await manager.update({'id': msg_id, 'text': ''}, mem_hash)
    return JSONResponse({'error': ''}, 200)


async def get_messages_endpoint(request: Request) -> Response:
    if (not authenticated(request.cookies, request.query_params.get('sender')) or not
    verify_token(request.query_params.get('token'), request.query_params.get('sender'))):
        return JSONResponse({'error': 'Forbidden', 'code': 403}, 403)
    print(request.query_params)
    msg_max = db.messages.count_documents({'hash': int(request.query_params.get('hash'))})-int(request.query_params.get('skip'))
    print(msg_max)
    if msg_max <= 0:
        return JSONResponse([], 200)
    messages = db.messages.find({'hash': int(request.query_params.get('hash'))}, projection={"_id": 0}, limit=msg_max)
    messages = list(messages)[-20:]
    return JSONResponse(messages, 200)


async def create_conversation(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('sender')):
        return JSONResponse({'error': 'Forbidden', 'code': 403}, 403)
    members = data.get('members')
    mem_hash = hash_list(members)
    if db.conversations.find_one({'hash': mem_hash}):
        return JSONResponse({'error': 'Conversation already exists', 'code': 200}, 200)
    db.conversations.insert_one({
        'hash': mem_hash,
        'members': members
    })
    return JSONResponse({'error': '', 'hash': mem_hash}, 200)


async def create_event(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('sender')) or not verify_token(data.get('token'), data.get('sender')):
        return JSONResponse({'error': 'Forbidden', 'code': 403}, 403)
    members = data.get('members')



async def invalidate_token(request: Request) -> Response:
    data = await request.json()
    db.tokens.find_one_and_delete({'token': data.get('token')})
    return JSONResponse({'error': '', 'message': 'Success'}, 200)
