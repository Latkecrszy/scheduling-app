import random, string, datetime
from app.constants import db
from bson.datetime_ms import DatetimeMS


def gen_token(email: str = None) -> str:
    t = ''.join(random.choices(string.ascii_letters, k=20))
    while db.tokens.find_one({'token': t}) is not None:
        t = ''.join(random.choices(string.ascii_letters, k=20))

    if email:
        db.tokens.insert_one({'token': t, 'email': email})
    else:
        db.anonymous_tokens.insert_one({'token': t, 'timeField': DatetimeMS(datetime.datetime.now())})
    return t


def gen_session(email: str) -> str:
    session = ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10))], k=30))
    while db.sessions.find_one({'session_id': session}) is not None:
        session = ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10))], k=30))
    db.sessions.insert_one({'session_id': session, 'email': email})
    return session


def gen_msg_id() -> int:
    msg_id = random.randint(1000000, 9999999)
    while db.messages.find_one({'id': msg_id}) is not None:
        msg_id = random.randint(1000000, 9999999)
    return msg_id


def authenticated(cookies: dict, email: str) -> bool:
    try:
        return cookies.get('email') == email and cookies.get('session_id') in [i['session_id'] for i in db.sessions.find({'email': email})]
    except TypeError:
        return False


def verify_token(token: str, email: str) -> bool:
    return bool(db.tokens.find_one({'token': token, 'email': email}))


def verify_session_utility(session_id: str, email: str) -> dict[str, str]:
    response = bool(db.sessions.find_one({'email': email, 'session_id': session_id}, projection={"_id": 0}))
    return {'verified': str(response).lower()}


def get_conversation_id(members: dict) -> str:
    cid = db.conversations.find_one({'members': [members['sender'], members['recipient']]}) or db.conversations.find_one({'members': [members['recipient'], members['sender']]})
    if cid:
        cid = cid['_id']
    else:
        cid = db.conversations.insert_one({'members': [members['sender'], members['recipient']]}).inserted_id
    return str(cid)


def get_messages(mem_hash: int, quantity=20) -> list[dict[str, str]]:
    messages = list(db.messages.find({'hash': mem_hash}, projection={'_id': 0}).sort('date', -1).limit(quantity))
    messages = sorted(messages, key=lambda x: x['date'])
    return messages


def get_message(msg_id) -> dict[str, str]:
    return db.messages.find_one({'id': msg_id}, projection={'_id': 0})


def hash_list(members: list) -> int:
    return sum([sum([ord(j)**2 for j in i]) for i in members])