from aiohttp import web
import aiohttp
from helpers import *
import config

global cfg 
cfg = config.Config()

async def join(params):
    try:
        code = params['code']
        url = 'https://discord.com/api/oauth2/token'
        HEADERS = {
    'User-Agent' : "DiscordBot (bit.ly/ARKBot, IDK I won't update this)",
    'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
    'client_id': cfg.client_id,
    'client_secret': cfg.client_secret,
    'grant_type': 'authorization_code',
    'code': code,
    'redirect_uri': cfg.redirect_url,
    'scope': 'bot guilds.join'
        }
        async with aiohttp.request("POST", url, headers=HEADERS , data=data) as resp:
            data = await resp.json()
            auth ={
                'Authorization' : f'Bearer {data["access_token"]}',
                'Content-Type': 'application/json',
                'User-Agent' : "DiscordBot (bit.ly/ARKBot, IDK I won't update this)"
            }
            bot_auth = {
                'Authorization' : f'Bot {cfg.token}',
                'Content-Type': 'application/json',
                'User-Agent' : "DiscordBot (bit.ly/ARKBot, IDK I won't update this)"
            }
            async with aiohttp.request("GET", f'https://discord.com/api/v6/users/@me', headers=auth) as resp2:
                data2 = await resp2.json()
                print(data2)
                async with aiohttp.request("PUT", f'https://discord.com/api/v6/guilds/723121116012347492/members/{data2["id"]}', headers=bot_auth, data=json.dumps({'access_token':data["access_token"]})) as resp3:
                    print(await resp3.json())
    except KeyError as e:
        print(e)
        return

async def index(request):
    params = request.rel_url.query
    await join(params)
    raise web.HTTPFound(location='https://discord.com/oauth2/authorized')

app = web.Application()
app.router.add_get('/', index)
web.run_app(app, host='0.0.0.0', port=80)