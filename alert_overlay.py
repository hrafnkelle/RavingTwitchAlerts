from aiohttp import web
import aiohttp
import hmac
import os

from aiohttp.web_middlewares import middleware
from aiohttp.web_ws import WebSocketResponse


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
    if messageType == "webhook_callback_verification":
        print("Verifying webhook")
        return web.Response(text=body['challenge'])
    elif messageType == 'webhook_callback_verification_pending':
        print(await request.json())
        return web.Response(text="Danke")
    else:
        event = body['event']
        type = body['subscription']['type']
        print(f'receiving {type} req for {event["broadcaster_user_name"]}')
        print(event)
        print("app = ", app)
        to_delete = []
        for ws in request.app['ws']:
            try:
                await ws.send_json(body)
            except:
                to_delete.append(ws)
        ws: WebSocketResponse
        for ws in to_delete:
            print(f"removing {ws}")
            request.app['ws'].remove(ws)
 
        return web.Response(text="Takk")

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


app = web.Application(middlewares=[verifyTwitchSignature])
app['ws'] = []
app.add_routes([web.get('/', hello),
                web.post('/webhooks/callback', webhook),
                web.get('/ws', websocketHandler),
                web.static('/overlay', 'static/')])
print("app=",app)
web.run_app(app, port=3000)