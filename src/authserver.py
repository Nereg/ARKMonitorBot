from aiohttp import web

async def join(params):
    try:
        code = params['code']
        url = 'https://discord.com/api/oauth2/token'
        HEADERS = {
    'User-Agent' : "Magic Browser",
    'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
    'client_id': 713272720053239808,
    'client_secret': 'ewIFngV9__rEDYMAskJUMCEG7118Erxu',
    'grant_type': 'authorization_code',
    'code': code,
    'redirect_uri': 'https://arkbot.pp.ua/',
    'scope': 'bot guilds.join'
        }
        async with aiohttp.request("POST", url, headers=HEADERS , data=data) as resp:
            print(resp.json())
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