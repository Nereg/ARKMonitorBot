import classes as c # our classes
from helpers import * # our helpers
from config import Config as conf # config
import discord # main discord libary
from discord.ext import commands # import commands extension
import commands as cmd # import all our commands
from menus import *
from server_cmd import *
from tasks import *
from discord.ext import menus
# classes.py - just classes for data shareing and processing
# config.py - main bot config
# commands.py - all commands live here
# helpers.py - helper funtions (like work with DB)

debug = Debuger('main') # create debuger (see helpers.py)
conf = conf() # load config
bot = commands.Bot(command_prefix=get_prefix,help_command=None) # create bot with default prefix and no help command
debug.debug('Inited DB and Bot!') # debug into console !
t = c.Translation() # load default english translation
#list of commands to implement
#help - default help command (just a help command)
#server - many commands for ark server
#server add - add server to monitoring # done
#server info - get info about server (some already added sorver or you could enter ip:port ?) 
#add - spits out link with invite !

#@bot.on_message
#async def on_message(message):
#    await message.channel.send(t.l['curr_prefix'].format(get_prefix(bot,message)))
#    if (message.author == bot.user):
#        return
#    else:
#        await message.channel.send(t.l['curr_prefix'].format(get_prefix(bot,message)))
#        for user in message.mentions:
#            if user == bot.user:
#                await message.channel.send(t.l['curr_prefix'].format(get_prefix(bot,message)))
#                return
                
@bot.command()
async def help(ctx):
    await ctx.send(t.l['help'].format(prefix=ctx.prefix))
#
#@bot.command()
#async def server(ctx, mode, *args): # redirect all parameters into our function
#    await cmd.server.server(ctx,mode,args)

bot.add_cog(ServerCmd(bot))
bot.add_cog(Updater(bot))

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
            data = makeRequest('SELECT * FROM Settings WHERE GuildId = ?',[str(ctx.guild.id)])
            if(data.__len__() > 0):
                data = data[0][2]
                makeRequest('UPDATE Settings SET Prefix=? WHERE GuildId=?',[prefix,str(ctx.guild.id)])
            else:
                data = c.GuildSettings(prefix).toJSON()
                makeRequest('INSERT INTO settings (GuildId,Prefix) VALUES (?,?)',[str(ctx.guild.id),prefix])    
            await  ctx.send(t.l['done']) #https://discordpy.readthedocs.io/en/latest/ext/commands/api.html?highlight=commands#discord.ext.commands.Bot.command_prefix


@bot.command()
async def share(ctx):
    await ctx.send(t.l['share_msg'].format(conf.inviteUrl))

@bot.command()
async def watch(ctx): # same
    selector = Selector(ctx,bot,c.Translation())
    server = await selector.select()
    if server == '':
        return
    makeRequest('INSERT INTO notifications (Ip,DiscordId,Type) VALUES (?,?,?)',[server.ip,ctx.channel.id,1])
    await ctx.send(t.l['done'])

#@bot.command()
#async def test(ctx):
#    selector = Selector(ctx,bot)
#    server = await selector.select()
#    print(server)

bot.run(conf.token) # get our discord token and FIRE IT UP !