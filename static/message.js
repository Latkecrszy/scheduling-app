let timestamps = {};
function onLoad() {
    let webSocket = new WebSocket(`ws://127.0.0.1:8000/database_ws?sender=${encodeURIComponent(sender)}&hash=${hash}&members=${members}`)
    webSocket.onmessage = async (e) => {
        let messages = JSON.parse(e.data)
        // If we only receive one message and the id already exists, it means it's a delete or edit operation
        if (messages.length === 1 && document.getElementById((messages[0].id).toString())) {
            let message = messages[0]
            if (message.text === '') {
                document.getElementById((message.id).toString()).remove()
            } else {
                document.getElementById((message.id)).innerText = message.text
            }
            return
        }
        messages.forEach(e => {
            let elements = createMessage(e)
            if (e.sender === sender) {
                document.getElementById('sent').appendChild(elements[0])
                document.getElementById('received').appendChild(elements[1])
            } else {
                document.getElementById('received').appendChild(elements[0])
                document.getElementById('sent').appendChild(elements[1])
            }
        })
        document.getElementById('scroller').scrollIntoView()
    }
    document.getElementById('message-box').addEventListener('keydown', sendMessage)
    document.addEventListener('scrollend', checkLoad)
}


function isScrolledIntoView(el) {
    let rect = el.getBoundingClientRect();
    return (rect.top >= 0) && (rect.bottom <= window.innerHeight);
}


async function checkLoad() {
    let keys = []
    for (let key of Object.keys(timestamps)) {
        keys.push(parseFloat(key))
    }
    let id = timestamps[Math.min(...keys).toString()]
    let el = document.getElementById(id)
    if (isScrolledIntoView(el)) {

        let messages = await fetch(`/get-messages?token=${token}&sender=${encodeURIComponent(sender)}&hash=${hash}&count=20&skip=${Object.keys(timestamps).length}`)
            .then(response => response.json())
        if (messages.length === 0) {
            return
        }
        messages.reverse()
        messages.forEach(e => {
            let elements = createMessage(e)
            if (e.sender === sender) {
                document.getElementById('sent').prepend(elements[0])
                document.getElementById('received').prepend(elements[1])
            } else {
                document.getElementById('received').prepend(elements[0])
                document.getElementById('sent').prepend(elements[1])
            }
        })
        el.scrollIntoView()
        window.scrollBy(0, -90)
    }
}


function createMessage(e) {
    let message = document.createElement('p')
    message.classList.add('message')
    let placeholder = document.createElement('p')
    placeholder.classList.add('placeholder')
    message.id = e.id
    message.setAttribute('timestamp', e.date)
    timestamps[e.date] = e.id
    message.innerText = e.text
    placeholder.innerText = e.text
    return [message, placeholder]
}


async function sendMessage(e) {
    if (e.keyCode === 13) {
        await fetch('/send-message', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({'token': token, 'sender': sender, 'members': members, 'hash': hash, 'text': document.getElementById('message-box').value})
        })
        document.getElementById('message-box').value = ''
    }
}