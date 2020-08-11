import classes as c # our classes
from helpers import * # our helpers
import config  # config
import discord # main discord libary
from discord.ext import commands # import commands extension
import commands as cmd # import all our commands
from menus import *
from server_cmd import *
from tasks import *
import json 
import traceback
import time
from datetime import datetime
import dbl_cog
import os 
import admin_cog
from discord import permissions
from discord.ext.commands import has_permissions, CheckFailure
import test
import notifications
# classes.py - just classes for data shareing and processing
# config.py - main bot config
# commands.py - all commands live here
# helpers.py - helper funtions (like work with DB)

debug = Debuger('main') # create debuger (see helpers.py)
conf = config.Config() # load config
game = discord.Game('ping me to get prefix')
bot = commands.Bot(command_prefix=get_prefix,help_command=None,activity=game) # create bot with default prefix and no help command
debug.debug('Inited DB and Bot!') # debug into console !
t = c.Translation() # load default english translation

bot.loop.set_debug(conf.debug)



@bot.command()
async def help(ctx):
    await ctx.send(t.l['help'].format(prefix=ctx.prefix))
#
#@bot.command()
#async def server(ctx, mode, *args): # redirect all parameters into our function
#    await cmd.server.server(ctx,mode,args)

bot.add_cog(ServerCmd(bot))
bot.add_cog(cmd.BulkCommands(bot))
bot.add_cog(notifications.NotificationComands(bot))
bot.add_cog(admin_cog.Admin(bot))
bot.add_cog(dbl_cog.TopGG(bot)) # will add when my bot approved by DBL see dbl.py for code and config string
bot.add_cog(test.Notifications(bot))
# and msg.author != bot.user
@bot.event
async def on_message(msg):
    if msg.content == f'<@!{bot.user.id}>' or  msg.content == f'<@{bot.user.id}>':
        await msg.channel.send(t.l['curr_prefix'].format(get_prefix(bot,msg)))
        return
    await bot.process_commands(msg)

@bot.command()
async def prefix(ctx,*args):
    print(args)
    if (args.__len__() <= 0):
        await ctx.send(t.l['curr_prefix'].format(ctx.prefix))
        return
    else:
        Permissions = ctx.author.permissions_in(ctx.channel)
        needed_perms =  permissions.Permissions(manage_roles=True)
        if (needed_perms <= Permissions):
            prefix = args[0]
            if (ctx.guild == None):
                await ctx.send(t.l['cant_change_prefix'])
                return
            else:
                data = makeRequest('SELECT * FROM settings WHERE GuildId = %s',(ctx.guild.id,))
                if(data.__len__() > 0):
                    makeRequest('UPDATE settings SET Prefix=%s WHERE GuildId=%s',(prefix,ctx.guild.id,))
                else:
                    makeRequest('INSERT INTO settings (GuildId,Prefix,Type) VALUES (%s,%s,0)',(ctx.guild.id,prefix,))    
                await  ctx.send(t.l['done']) #https://discordpy.readthedocs.io/en/latest/ext/commands/api.html?highlight=commands#discord.ext.commands.Bot.command_prefix
        else:
            await ctx.send('You need manage roles permission to change my prefix!')
            return

#@bot.event
async def on_command_error1(ctx,error):
    print(error)
    try:
        await on_command_error1(ctx,error)
    except BaseException  as e:
        print('Error in  handler!')
        print(e)

@bot.event
async def on_command_error(ctx,error):
    if (type(error) == discord.ext.commands.errors.CommandNotFound):
        await ctx.send('You entered wrong command ! You can list all my commands with `{}help`'.format(ctx.prefix))
        return
    if (type(error) == discord.ext.commands.errors.CheckFailure):
        return
    if (type(error) == discord.ext.commands.errors.NotOwner):
        meUser = bot.get_user(277490576159408128)
        meDM = await meUser.create_dm()
        await meDM.send(f'Someone tried used only admin command ! It was `{ctx.message.content}`')
        return
    if (type(error) == discord.ext.commands.CommandOnCooldown):
        message = f'''
Hold down !
You can use `{ctx.message.content}` command
Only {error.cooldown.rate} times per {int(error.cooldown.per)} seconds!
Try later.
        '''
        await ctx.send(message)
        return
    if (type(error) == discord.ext.commands.errors.MissingPermissions):
        await ctx.send(error)
        return
    errors = traceback.format_exception(type(error), error, error.__traceback__)
    Time = int(time.time())
    makeRequest('INSERT INTO errors(Error, Time, UserDiscordId, ChannelDiscordId, GuildDiscordId, Message) VALUES (%s,%s,%s,%s,%s,%s)',(json.dumps(errors),Time,ctx.author.id,ctx.channel.id,ctx.guild.id,ctx.message.content,))
    data = makeRequest('SELECT * FROM errors WHERE Time=%s',(Time,))
    Id = data[0][0]
    meUser = bot.get_user(277490576159408128)
    await ctx.send(f'Error occured ! I logged in and notified my creator. Your unique error id is `{Id}`. Report this error to @StormyQ#5109')
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
@commands.is_owner()
@commands.cooldown(1, 60, type=commands.BucketType.user)
async def test(ctx):
    await ctx.send('test')

bot.run(conf.token) # get our discord token and FIRE IT UP !