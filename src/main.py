import classes as c # our classes
from helpers import * # our helpers
from config import Config as conf # config
import discord # main discord libary
from discord.ext import commands # import commands extension
import commands as cmd # import all our commands
from menus import *
from server_cmd import *
from tasks import *
# classes.py - just classes for data shareing and processing
# config.py - main bot config
# commands.py - all commands live here
# helpers.py - helper funtions (like work with DB)

debug = Debuger('main') # create debuger (see helpers.py)
conf = conf() # load config
bot = commands.Bot(command_prefix=conf.defaultPrefix,help_command=None) # create bot with default prefix and no help command
debug.debug('Inited DB and Bot!') # debug into console !

#list of commands to implement
#help - default help command (just a help command)
#server - many commands for ark server
#server add - add server to monitoring # done
#server info - get info about server (some already added sorver or you could enter ip:port ?) 
#add - spits out link with invite !


@bot.command()
async def help(ctx):
    await ctx.send('''
`!server info` - get data about server if wothout ip will prompt you to select server  
`!server add` - suply ip adress to add server to bot's list 
`!list` - list all servers in bot's list
    ''')
#
#@bot.command()
#async def server(ctx, mode, *args): # redirect all parameters into our function
#    await cmd.server.server(ctx,mode,args)

bot.add_cog(ServerCmd(bot))
bot.add_cog(Updater())

@bot.command()
async def list(ctx): # same
    await cmd.list_servers(ctx)

@bot.command()
async def ping(ctx):
    time = int(bot.latency * 1000)
    await ctx.send(f'Pong! Ping is: {time} ms')

@bot.command()
async def share(ctx):
    await ctx.send('Here is link {} to invite me to our server! Also you can DM me !'.format(conf.inviteUrl))

@bot.command()
async def test(ctx):
    selector = SelectServerMenu()
    server = await selector.prompt(ctx)
    debug = Debuger('test')
    debug.debug(server)
    info = c.ARKServer(server.ip)
    info = info.GetInfo()
    print(info.ping)

bot.run(conf.token) # get our discord token and FIRE IT UP !