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
    'User-Agent' : "Magic Browser",
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
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            async with aiohttp.request("GET", f'https://discord.com/api/v6/users/@me', headers=auth) as resp2:
                print(await resp2.json())
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