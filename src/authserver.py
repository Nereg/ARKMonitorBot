from aiohttp import web
import aiohttp
from helpers import *
import config
import json

global cfg 
cfg = config.Config()

async def handle_500(request):
    return web.Response(html='<h1>Oooops! Error happened!</h1>\n <b> Please report it to <a href="https://bit.ly/ARKDiscord" target="_blank">this</a> support guild!</b>\n Also <a href="https://discord.com/oauth2/authorize?client_id=713272720053239808&permissions=1141189696&&scope=bot" target="_blank">here</a> is normal invite link. You can use that now')


def create_error_middleware(overrides):

    @web.middleware
    async def error_middleware(request, handler):

        try:
            response = await handler(request)

            override = overrides.get(response.status)
            if override:
                return await override(request)

            return response

        except web.HTTPException as ex:
            override = overrides.get(ex.status)
            if override:
                return await override(request)

            raise

    return error_middleware


def setup_middlewares(app):
    error_middleware = create_error_middleware({
        500: handle_500
    })
    app.middlewares.append(error_middleware)

async def join(params):
    try:
        code = params['code']
        url = 'https://discord.com/api/oauth2/token'
        HEADERS = {
    'User-Agent' : "DiscordBot (cutt.ly/ARKBot, IDK I won't update this)",
    'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
    'client_id': cfg.client_id,
    'client_secret': cfg.client_secret,
    'grant_type': 'authorization_code',
    'code': code,
    'redirect_uri': cfg.redirect_url,
    'scope': 'bot guilds.join identify'
        }
        async with aiohttp.request("POST", url, headers=HEADERS , data=data) as resp:
            data = await resp.json()
            
            print(data)
            auth ={
                'Authorization' : f'Bearer {data["access_token"]}',
                'Content-Type': 'application/json',
                'User-Agent' : "DiscordBot (cutt.ly/ARKBot, IDK I won't update this)"
            }
            bot_auth = {
                'Authorization' : f'Bot {cfg.token}',
                'Content-Type': 'application/json',
                'User-Agent' : "DiscordBot (cutt.ly/ARKBot, IDK I won't update this)"
            }
            async with aiohttp.request("GET", f'https://discord.com/api/v6/users/@me', headers=auth) as resp2:
                data2 = await resp2.json()
                print(data2)
                if ('locale' in data2):
                    locale = data2['locale']
                else:
                    locale = None
                users = makeRequest('SELECT Id FROM users WHERE Id=%s',(data2['id'],))
                if (users.__len__() <= 0):
                    makeRequest('INSERT INTO users(DiscordId, RefreshToken, Locale, DiscordName) VALUES (%s,%s,%s,%s)',(data2['id'],data['refresh_token'],locale,data2['username']))
                async with aiohttp.request("PUT", f'https://discord.com/api/v6/guilds/723121116012347492/members/{data2["id"]}', headers=bot_auth, data=json.dumps({'access_token':data["access_token"]})) as resp3:
                    print('lol')
    except KeyError as e:
        print(e)
        return

async def index(request):
    params = request.rel_url.query
    await join(params)
    raise web.HTTPFound(location='https://discord.com/oauth2/authorized', headers={'Server': 'NotYourBusiness'})

app = web.Application()
app.router.add_get('/', index)
setup_middlewares(app)
web.run_app(app, host='0.0.0.0', port=80)