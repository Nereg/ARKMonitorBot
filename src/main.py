import classes as c # our classes
from helpers import * # our helpers
import config  # config
import discord # main discord libary
from discord.ext import commands # import commands extension
import commands as cmd # import all our commands
from menus import *
from server_cmd import *
from tasks import *
from discord.ext import menus
import json 
import traceback
import time
from datetime import datetime
import migration
# classes.py - just classes for data shareing and processing
# config.py - main bot config
# commands.py - all commands live here
# helpers.py - helper funtions (like work with DB)

debug = Debuger('main') # create debuger (see helpers.py)
conf = config.Config() # load config
bot = commands.Bot(command_prefix=get_prefix,help_command=None) # create bot with default prefix and no help command
debug.debug('Inited DB and Bot!') # debug into console !
t = c.Translation() # load default english translation
#list of commands to implement
#help - default help command (just a help command)
#server - many commands for ark server
#server add - add server to monitoring # done
#server info - get info about server (some already added sorver or you could enter ip:port ?) 
#add - spits out link with invite !




@bot.command()
async def help(ctx):
    await ctx.send(t.l['help'].format(prefix=ctx.prefix))
#
#@bot.command()
#async def server(ctx, mode, *args): # redirect all parameters into our function
#    await cmd.server.server(ctx,mode,args)

bot.add_cog(ServerCmd(bot))
#bot.add_cog(Updater(bot))

@bot.command()
async def list(ctx): # same
    await cmd.list_servers(ctx)

@bot.command()
async def ping(ctx):
    time = int(bot.latency * 1000)
    await ctx.send(t.l['ping'].format(time))

@bot.command()
async def prefix(ctx,*args):
    print(args)
    if (args.__len__() <= 0):
        await ctx.send(t.l['curr_prefix'].format(ctx.prefix))
        return
    else:
        prefix = args[0]
        if (ctx.guild == None):
            await ctx.send(t.l['cant_change_prefix'])
            return
        else:
            data = makeRequest('SELECT * FROM settings WHERE GuildId = %s',(ctx.guild.id,))
            if(data.__len__() > 0):
                makeRequest('UPDATE Settings SET Prefix="%s" WHERE GuildId=%s',(prefix,ctx.guild.id,))
            else:
                makeRequest('INSERT INTO settings (GuildId,Prefix,Type) VALUES (%s,%s,1)',(ctx.guild.id,prefix,))    
            await  ctx.send(t.l['done']) #https://discordpy.readthedocs.io/en/latest/ext/commands/api.html?highlight=commands#discord.ext.commands.Bot.command_prefix

@bot.event
async def on_command_error(ctx,error):
    if (type(error) == discord.ext.commands.errors.CommandNotFound):
        await ctx.send('You entered wrong command ! You can list all my commands with `{}help`'.format(ctx.prefix))
        return
    errors = traceback.format_exception(type(error), error, error.__traceback__)
    Time = int(time.time())
    makeRequest('INSERT INTO errors(Error, Time, UserDiscordId, ChannelDiscordId, GuildDiscordId, Message) VALUES (%s,%s,%s,%s,%s,%s)',(json.dumps(errors),Time,ctx.author.id,ctx.channel.id,ctx.guild.id,ctx.message.content,))
    data = makeRequest('SELECT * FROM errors WHERE Time=%s',(Time,))
    Id = data[0][0]
    await ctx.send(f'Error occured ! I logged in and notified my creator. Your unique error id is `{Id}`. You can message my creator олег#3220 or report this error to my support discord server ! You can join it by this link : https://discord.gg/qvzYArS')
    meUser = bot.get_user(277490576159408128)
    meDM = await meUser.create_dm()
    errors_str = ''.join(errors)
    date = datetime.utcfromtimestamp(Time).strftime('%Y-%m-%d %H:%M:%S')
    message = f'''
{meUser.mention}
Произошов пиздец !
`{errors_str}`
Айдишник еррора : `{Id}`
Сообщение : `{ctx.message.content}`
Ошибка произошла : `{date}`
    '''
    await meDM.send(message)

@bot.command()
async def share(ctx):
    await ctx.send(t.l['share_msg'].format(conf.inviteUrl))

@bot.command()
async def watch(ctx): # same
    #selector = Selector(ctx,bot,c.Translation())
    #server = await selector.select()
    #if server == '':
    #    return
    #makeRequest('INSERT INTO `notifications`(`Type`, `Data`) VALUES (%s,%s)',(1,json.dumps([ctx.channel.id,server.ip])))
    await ctx.send('Something will be here but not now ;)')

@bot.command()
async def test(ctx):
    raise Exception('Test')

bot.run(conf.token) # get our discord token and FIRE IT UP !