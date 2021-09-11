from aiohttp import web
import aiohttp
import hmac
import os
import logging

from aiohttp.web_middlewares import middleware
from aiohttp.web_ws import WebSocketResponse

LOG_FILENAME = 'twitch.log'

try:
    TWITCH_CLIENT_ID = os.environ["TWITCH_CLIENT_ID"]
    TWITCH_CLIENT_SECRET = os.environ["TWITCH_CLIENT_SECRET"]
except KeyError:
    print("Make sure TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET are set as environment")
    exit(-1)

async def hello(request):
    return web.Response(text="Hello, world")

@middleware
async def verifyTwitchSignature(req: web.Request, handler):
    messageId = req.headers.get('Twitch-Eventsub-Message-Id',None)
    if messageId is None:
        print("No message id")
        return await handler(req)
    else:
        messageId = messageId.encode()
    timestamp = req.headers['Twitch-Eventsub-Message-Timestamp'].encode()
    messageSignature = req.headers['Twitch-Eventsub-Message-Signature']

    twitchSigningSecret = TWITCH_CLIENT_SECRET.encode()

    resp = await handler(req)

    c=hmac.new(twitchSigningSecret, digestmod='sha256')
    c.update(messageId)
    c.update(timestamp)
    c.update(await req.read())
    computedSignature = "sha256="+c.hexdigest()

#    print(f'Recv sig {messageSignature}, comp sig {computedSignature}')
    
    if computedSignature!=messageSignature:
        return web.Response(status=403, reason="verification failed")
    return resp

async def webhook(request: web.Request):
    messageType = request.headers['Twitch-Eventsub-Message-Type']
    body = await request.json()
    logging.debug(request.headers)
    logging.debug(await request.text())
    if messageType == "webhook_callback_verification":
        print("Verifying webhook")
        return web.Response(text=body['challenge'])
    elif messageType == 'webhook_callback_verification_pending':
        print(await request.json())
        return web.Response(text="Danke")
    else:
        event = body['event']
        type = body['subscription']['type']
        print(f'receiving {type} req for {event.get("broadcaster_user_name","Unknown")}')
        print(event)
        await sendToWebsockets(request, body)
        return web.Response(text="Takk")

async def sendToWebsockets(request, data):
    to_delete = []
    for ws in request.app['ws']:
        try:
            await ws.send_json(data)
        except:
            to_delete.append(ws)
    ws: WebSocketResponse
    for ws in to_delete:
        print(f"removing {ws}")
        request.app['ws'].remove(ws)


async def websocketHandler(request: web.Request):
    ws = WebSocketResponse()
    request.app['ws'].append(ws)
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
                print('ws closed')
            else:
                await ws.send_str(msg.data + '/answer')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' % ws.exception())
            
    print('websocket connection closed')
    return ws

async def authHandler(request: web.Request):
    for k,v in request.rel_url.query:
        print(f'{k}:{v}')
    logging.info(request.query_string)
    return web.Response(text='AuthReceived')

async def injectHandler(request: web.Request):
    body = await request.json()
    await sendToWebsockets(request, body)
    return web.Response(text='OK Boomer')

app = web.Application(middlewares=[verifyTwitchSignature])
app['ws'] = []
app.add_routes([web.post('/webhooks/callback', webhook),
                web.post('/inject', injectHandler),
                web.get('/ws', websocketHandler),
                web.get('/auth', authHandler),
                web.static('/overlay', 'static/')])
logging.basicConfig(level=logging.DEBUG, filename=LOG_FILENAME)
console = logging.StreamHandler()  
console.setLevel(logging.INFO)  
logging.getLogger("").addHandler(console)
web.run_app(app, port=3000)
