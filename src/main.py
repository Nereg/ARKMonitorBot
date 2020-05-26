import classes as c # our classes
from helpers import * # our helpers
from config import Config as conf # config
import discord # main discord libary
from discord.ext import commands # import commands extension
import commands as cmd # import all our commands

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
    await ctx.send('Это сообщение хелпа :/')

@bot.command()
async def server(ctx, mode, ip): # redirect all parameters into our function
    await cmd.server(ctx,mode,ip)

@bot.command()
async def list(ctx): # same
    await cmd.list_servers(ctx)

@bot.command()
async def ping(ctx):
    basetime= arrow.get(0)
    time = arrow.get(bot.latency)
    time = time - basetime
    await ctx.send('Pong! Ping is: {}'.format(time))

@bot.command()
async def share(ctx):
    await ctx.send('Here is link {} to invite me to our server! Also you can DM me !'.format(conf.inviteUrl))

bot.run(conf.token) # get our discord token and FIRE IT UP !