import classes as c # our classes
from helpers import * # our helpers
import config  # config
import discord # main discord libary
from discord.ext import commands # import commands extension
import commands as cmd # import all our commands
from menus import *
from server_cmd import *
from discord.ext import menus
import json 
import traceback
import time
from datetime import datetime
import dbl_cog
import os 
import admin_cog
from discord import permissions
from discord.ext.commands import has_permissions, CheckFailure
import updater
import automessage
# classes.py - just classes for data shareing and processing
# config.py - main bot config
# commands.py - all commands live here
# helpers.py - helper funtions (like work with DB)

debug = Debuger('main') # create debuger (see helpers.py)
conf = config.Config() # load config
game = discord.Game('ping me to get prefix')
# ARK:SE app id in discord : 356887282982191114 
#game = discord.Activity(application_id=713272720053239808,name='test',url='',type=discord.ActivityType.playing,state="state",details='details',timestamps={'start':123456789010,'end':123132143254356},assets={'large_image':'empty_logo','large_text':'test','small_image':'empty_logo','small_text':'test'})
bot = commands.Bot(command_prefix=get_prefix,help_command=None,activity=game) # create bot with default prefix and no help command
debug.debug('Inited DB and Bot!') # debug into console !
t = c.Translation() # load default english translation

bot.loop.set_debug(conf.debug)

@bot.command()
async def help(ctx):
    #await ctx.send(t.l['help'].format(prefix=ctx.prefix,version=conf.version)) # ha old small version SUCKS lol 
    time = datetime(2000,1,1,0,0,0,0)
    message = discord.Embed(title='List of commands',timestamp=time.utcnow())
    empty = 'test'
    prefix = await get_prefix(bot,ctx.message)
    isInline=False
    message.set_footer(text=f'Requested by {ctx.author.name} • Bot {conf.version} • GPLv3 ',icon_url=ctx.author.avatar_url)
    serverValue = f'**`{prefix}server info`- select and view info about added server\n`{prefix}server add <IP>:<Query port>`- add server to your list\n`{prefix}server delete`- delete server from your list\n`{prefix}server alias`- list aliases for your servers\n`{prefix}server alias`- list aliases for your servers\n`{prefix}server alias "<Alias>"`- select and add alias for server\n`{prefix}server alias delete`- delete alias for your server**'
    message.add_field(name=f'**Server group:**',value=serverValue)
    #message.add_field(name=f'`{prefix}server info`- select and view info about added server',value=empty,inline=isInline)
    #message.add_field(name=f'`{prefix}server add <IP>:<Query port>`- add server to your list',value=empty,inline=isInline)
    #message.add_field(name=f'`{prefix}server delete`- delete server from your list',value=empty,inline=isInline)
    #message.add_field(name=f'`{prefix}server alias`- list aliases for your servers',value=empty,inline=isInline)
    #message.add_field(name=f'`{prefix}server alias "<Alias>"`- select and add alias for server',value=empty,inline=isInline)
    #message.add_field(name=f'`{prefix}server alias delete`- delete alias for your server',value=empty,inline=isInline)
    notificationsValue = f'**`{prefix}watch`- select server and bot will send a message when it goes online/offline in current channel\n`{prefix}unwatch` - undone what `{prefix}watch` command do**'
    message.add_field(name=f'**Notifications:**',value=notificationsValue,inline=isInline)
    #message.add_field(name=f'`{prefix}watch`- select server and bot will send a message when it goes online/offline in current channel',value=empty,inline=isInline)
    #message.add_field(name=f'`{prefix}unwatch` - undone what `{prefix}watch` command do',value=empty,inline=isInline)
    miscValue =f'**`{prefix}info`- get info about this bot (e.g. support server, github etc.)**'
    message.add_field(name=f'**Miscellaneous:**',value=miscValue,inline=isInline)
    #message.add_field(name=f'`{prefix}info`- get info about this bot (e.g. support server, github etc.)',value=empty,inline=isInline)
    await ctx.send(embed=message)

bot.add_cog(ServerCmd(bot))
bot.add_cog(cmd.BulkCommands(bot))
bot.add_cog(admin_cog.Admin(bot))
bot.add_cog(dbl_cog.TopGG(bot))
bot.add_cog(updater.Updater(bot))
bot.add_cog(automessage.Automessage(bot))

@bot.event
async def on_message(msg):
    if msg.content == f'<@!{bot.user.id}>' or  msg.content == f'<@{bot.user.id}>':
        await msg.channel.send(t.l['curr_prefix'].format(await get_prefix(bot,msg)))
        return
    await bot.process_commands(msg)
    
@commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True)
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
                if('@' in prefix):
                    await ctx.send('You can`t set prefix that contains @!')
                    return
                data = makeRequest('SELECT * FROM settings WHERE GuildId = %s',(ctx.guild.id,))
                if(data.__len__() > 0):
                    makeRequest('UPDATE settings SET Prefix=%s WHERE GuildId=%s',(prefix,ctx.guild.id,))
                else:
                    makeRequest('INSERT INTO settings (GuildId,Prefix,Type) VALUES (%s,%s,0)',(ctx.guild.id,prefix,))    
                await  ctx.send(t.l['done']) #https://discordpy.readthedocs.io/en/latest/ext/commands/api.html?highlight=commands#discord.ext.commands.Bot.command_prefix
        else:
            await ctx.send('You need manage roles permission to change my prefix!')
            return

@bot.event
async def on_command_error1(ctx,error):
    debug.debug('Entered second handler!')
    debug.debug(error)
    try:
        await on_command_error1(ctx,error)
    except BaseException  as e:
        debug.debug('Error in  handler!')
        debug.debug(e)

@bot.event
async def on_command_error(ctx,error):  
    debug.debug('Entered error handler')      
    meUser = bot.get_user(277490576159408128)
    meDM = await meUser.create_dm()
    if (type(error) == discord.ext.commands.errors.CommandNotFound):
        await ctx.send('You entered wrong command ! You can list all my commands with `{}help`'.format(ctx.prefix))
        return
    if (type(error) == discord.ext.commands.errors.CheckFailure):
        return
    if (type(error) == discord.ext.commands.errors.NotOwner):
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
    if (type(error) == discord.ext.commands.errors.BotMissingPermissions or type(error) == discord.errors.Forbidden): # hey wtf some reason (missing permissions) and two exeptions!
        needed_perms = "```Add reactions\nUse external reactions\nSend and read messages\nManage messages```"
        try:
            await ctx.send(f'Hey! Bot is missing some permissions! Bot needs:\n{needed_perms}')
        except discord.Forbidden:
            try:
                await ctx.author.send(f'Hey hello. You invited me to your `{ctx.guild.name}` guild and used `{ctx.message.content}` command. But I am missing some permissions! Most likely some channel permissions overrides bots one. I need:\n{needed_perms}')
            except BaseException:
                return
        return
    errors = traceback.format_exception(type(error), error, error.__traceback__)
    Time = int(time.time())
    makeRequest('INSERT INTO errors(Error, Time, UserDiscordId, ChannelDiscordId, GuildDiscordId, Message) VALUES (%s,%s,%s,%s,%s,%s)',(json.dumps(errors),Time,ctx.author.id,ctx.channel.id,ctx.guild.id,ctx.message.content,))
    debug.debug('Made SQL')
    data = makeRequest('SELECT * FROM errors WHERE Time=%s',(Time,))
    Id = data[0][0]
    meUser = bot.get_user(277490576159408128)
    await ctx.send(f'Error occured ! I logged in and notified my creator. Your unique error id is `{Id}`. You can message my creator {meUser.name}#{meUser.discriminator} or report this error to my support discord server ! You can join it by this link : <https://bit.ly/ARKDiscord>')
    debug.debug('Sent channel message')
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
Имя гильдии : `{ctx.guild.name}`
    '''
    if (message.__len__() >= 2000):
        try:
            await meDM.send(message[:1975] + '`\nEnd of first part')
            await meDM.send(message[1975:-1])
        except BaseException as e:
            await meDM.send('Lenth of error message is over 4k!')
            await meDM.send(e)
    else:
        await meDM.send(message)

@bot.command()
async def share(ctx):
    await ctx.send(t.l['share_msg'].format(conf.inviteUrl))


@bot.command()
@commands.is_owner()
@commands.cooldown(1, 60, type=commands.BucketType.user)
@commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True)
async def test(ctx):
    await ctx.send(await getAlias(8,ctx.guild.id))

bot.run(conf.token) # get our discord token and FIRE IT UP !