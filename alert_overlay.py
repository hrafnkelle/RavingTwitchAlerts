import time
import random
import asyncio
import hmac
import os
import logging
import aiohttp
import yaml
from aiohttp import web
from aiohttp.web_middlewares import middleware
from aiohttp.web_ws import WebSocketResponse

from simtwitchbridge import SimTwitchBridge 
import airport

LOG_FILENAME = 'twitch.log'

try:
    TWITCH_CLIENT_ID = os.environ["TWITCH_CLIENT_ID"]
    TWITCH_CLIENT_SECRET = os.environ["TWITCH_CLIENT_SECRET"]
    TWITCH_BEARER_OAUTH = os.environ["TWITCH_BEARER_OAUTH"]
except KeyError:
    logging.error("Make sure TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET and TWITCH_BEARER_OAUTH are set as environment")
    for k,v in os.environ.items():
        logging.error(f"{k}:{v}")
    exit(-1)


@middleware
async def verifyTwitchSignature(req: web.Request, handler):
    messageId = req.headers.get('Twitch-Eventsub-Message-Id',None)
    if messageId is None:
        logging.debug("No message id")
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
    
    if computedSignature!=messageSignature:
        return web.Response(status=403, reason="verification failed")
    return resp

async def fulfilRedeption(broadcaster_id, reward_id, event_id):
    async with aiohttp.ClientSession() as session:
        headers = {'Content-tType': 'application/json',
                    'client-id': TWITCH_CLIENT_ID,
                    'Authorization': f"Bearer {TWITCH_BEARER_OAUTH}"}
        urlparam = {'broadcaster_id': broadcaster_id,
                        'reward_id': reward_id,
                        'id': event_id
                    }
        async with session.patch("https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions", headers=headers, params=urlparam, json={'status': 'FULFILLED'}) as resp:
            print(resp.status)
            print(await resp.text())

async def handleRewardRedemtionAdd(event):
    sim = app['sim'] # type: SimTwitchBridge
    sim.doReward(event['reward']['id'])

    await fulfilRedeption(event['broadcaster_user_id'], event['reward']['id'], event['id'])

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
        print(f'{messageType}: receiving {type} req for {event.get("broadcaster_user_name","Unknown")}')
        print(body)
        if type == "channel.channel_points_custom_reward_redemption.add":
            await handleRewardRedemtionAdd(event)
        await sendToWebsockets(request.app, {'type': 'twitch', 'event': body})
        return web.Response(text="Takk")    

async def sendToWebsockets(app, data):
    to_delete = []
    for ws in app['ws']:
        try:
            await ws.send_json(data)
        except:
            to_delete.append(ws)
    ws: WebSocketResponse
    for ws in to_delete:
        print(f"removing {ws}")
        app['ws'].remove(ws)


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


async def push_data(app):
    while True:
        dataset = app['sim'].getFlightStatusVars()
        if not dataset['connected']:
            print("No flightim connection")
        else:
            airport_id, distance = airport.getClosestAirport(dataset['PLANE_LATITUDE'], dataset['PLANE_LONGITUDE'])
            dataset['CLOSEST_AIRPORT_ID'] = airport_id
            dataset['CLOSEST_AIRPORT_DISTANCE'] = distance
        await sendToWebsockets(app, {'type': 'simconnect', 'event': dataset})
        await asyncio.sleep(2)


async def authHandler(request: web.Request):
    for k,v in request.rel_url.query:
        print(f'{k}:{v}')
    print(request.query_string)
    return web.Response(text='AuthReceived')        

async def start_background_tasks(app):
    asyncio.create_task(push_data(app))

async def authHandler(request: web.Request):
    for k,v in request.rel_url.query:
        print(f'{k}:{v}')
    logging.info(request.query_string)
    return web.Response(text='AuthReceived')

async def injectHandler(request: web.Request):
    body = await request.json()
    await sendToWebsockets(request, body)
    return web.Response(text='OK Boomer')    

app = web.Application()
app['ws'] = []
app['sim'] = SimTwitchBridge()
app.add_routes([web.get('/ws', websocketHandler),
                web.static('/overlay', 'static/'),
                web.get('/auth', authHandler),
                web.post('/webhooks/callback', webhook)])
app.on_startup.append(start_background_tasks)

web.run_app(app, port=3001)
