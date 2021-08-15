from charcoal import Charcoal
import classes as c  # our classes
from helpers import *  # our helpers
import config  # config
import discord  # main discord libary
from discord.ext import commands  # import commands extension
import commands as cmd  # import all our commands
from menus import *  # menus like selector of servers
from server_cmd import *  # !server command
import json  # json module
import traceback  # traceback
import time  # time
from datetime import datetime
import dbl_cog  # cog with top.gg updater
import os
import admin_cog  # cog with admin commands
from discord import permissions
from discord.ext.commands import has_permissions, CheckFailure
import updater  # cog with updater of servers in DB (main consern annoying AF)
import automessage  # cog with !automessage command and updater for it
import nest_asyncio
import campfire
from updatePlugins import notifications

# classes.py - just classes for data shareing and processing
# config.py - main bot config
# commands.py - all commands live here
# helpers.py - helper funtions (like work with DB)

debug = Debuger('main')  # create debuger (see helpers.py)
conf = config.Config()  # load config
# set custom status for bot (sadly it isn't possible to put buttons like in user's profiles)
game = discord.Game('ping me to get prefix')
# create auto sharded bot with default prefix and no help command
bot = commands.AutoShardedBot(
    command_prefix=get_prefix, help_command=None, activity=game)
debug.debug('Inited DB and Bot!')  # debug into console !
t = c.Translation()  # load default english translation

# if conf.debug is True asyncio will output additional debug info into logs
bot.loop.set_debug(conf.debug)


# add all cogs
bot.add_cog(ServerCmd(bot))
bot.add_cog(cmd.BulkCommands(bot))
bot.add_cog(admin_cog.Admin(bot))
bot.add_cog(dbl_cog.TopGG(bot))
##bot.add_cog(updater.Updater(bot))
bot.add_cog(updater.NeoUpdater(bot))
#bot.add_cog(automessage.Automessage(bot))
bot.add_cog(campfire.Campfire(bot))
bot.add_cog(Charcoal(bot))
bot.add_cog(notifications.NotificationsCog(bot))


# ~~~~~~~~~~~~~~~~~~~~~
#       COMMANDS
# ~~~~~~~~~~~~~~~~~~~~~

# !prefix command
# default permissions check
@commands.bot_has_permissions(add_reactions=True, read_messages=True, send_messages=True, manage_messages=True, external_emojis=True)
@bot.command()
async def prefix(ctx, *args):
    if (args.__len__() <= 0):  # if no additional parameters
        # send current prefix and return
        await ctx.send(t.l['curr_prefix'].format(ctx.prefix))
        return
    else:  # if not
        # get permissions of caller in current channel
        Permissions = ctx.author.permissions_in(ctx.channel)
        # set needed permissions (manage roles)
        needed_perms = permissions.Permissions(manage_roles=True)
        if (needed_perms <= Permissions):  # check permissions
            # if check successed
            # get new prefix from params
            prefix = args[0] 
            # if @ in prefix
            if('@' in prefix):
                # send error message
                await ctx.send('You can`t set prefix that contains @!')
                return
            # get settings for current guild
            data = await makeAsyncRequest(
                'SELECT * FROM settings WHERE GuildId = %s', (ctx.guild.id,))
            # if we have record for current guild
            if(data.__len__() > 0):
                # update it
                await makeAsyncRequest(
                    'UPDATE settings SET Prefix=%s WHERE GuildId=%s', (prefix, ctx.guild.id,))
            # else
            else:
                # create one
                await makeAsyncRequest(
                    'INSERT INTO settings (GuildId,Prefix,Type) VALUES (%s,%s,0)', (ctx.guild.id, prefix,))
            # send done message
            await ctx.send(t.l['done'])
        # if check failed
        else: 
            # send error message
            await ctx.send('You need manage roles permission to change my prefix!')
            return


#main help command
@bot.command()
async def help(ctx):
    time = datetime(2000, 1, 1, 0, 0, 0, 0)  # get time object
    # set title and timestamp of embed
    message = discord.Embed(title='List of commands',
                            timestamp=time.utcnow())  
    # get current prefix
    prefix = ctx.prefix
    # set footer for embed
    message.set_footer(text=f'Requested by {ctx.author.name} • Bot {conf.version} • GPLv3 ',
                       icon_url=ctx.author.avatar_url)
    # define value for Server section
    serverValue = f'''**`{prefix}server info`- select and view info about added server (only Steam servers both official and not)
`{prefix}server add <IP>:<Query port>`- add server to your list
`{prefix}server delete`- delete server from your list
`{prefix}server alias`- list aliases for your servers
`{prefix}server alias`- list aliases for your servers
`{prefix}server alias "<Alias>"`- select and add alias for server
`{prefix}server alias delete`- delete alias for your server**'''
    # add server section to the embed
    message.add_field(name=f'**Server group:**',
                      value=serverValue)  
    # define value for notifications section
    notificationsValue = f'''**`{prefix}watch`- select server and bot will send a message when it goes online/offline in current channel
`{prefix}unwatch` - undone what `{prefix}watch` command do 
`{prefix}automessage #any_channel` - bot will send and update message about some server!
`{prefix}automessage` - list any automessages you have
`{prefix}automessage delete` - delete all automessages for some server
**'''
    # add notifications section to the embed
    message.add_field(name=f'**Notifications:**', value=notificationsValue,
                      inline=False)  
    # define misc sections value
    miscValue = f'**`{prefix}info`- get info about this bot (e.g. support server, github etc.)**'
    # add misc section to the embed
    message.add_field(name=f'**Miscellaneous:**', value=miscValue,
                      inline=False)
    # and send it  
    await ctx.send(embed=message)  

# some old command
@bot.command()
async def share(ctx):
    await ctx.send(t.l['share_msg'].format(conf.inviteUrl))

# ~~~~~~~~~~~~~~~~~~~~~
#        EVENTS
# ~~~~~~~~~~~~~~~~~~~~~

# used to count executed commands
# doesn't work at all
@bot.event
async def on_command_completion(ctx):
    name = ctx.command.name  # extract name of command
    if (name == 'server'):  # if it is a server command (I am too lazy to chop the into subcommands or smth like that)
        try:
            command = ctx.args[2]  # get the "subcommand"
        except IndexError:  # that happens if we write just //server
            return
        correctCommands = ['add', 'info', 'delete',
                           'alias']  # list of valid "subcommands"
        if (command not in correctCommands):  # if it isn't correct
            return  # return
        else:  # else
            name += ' ' + command  # append name of "subcommand" to main name
    # CREATE TABLE `bot`.`commandsused` ( `Id` INT NOT NULL AUTO_INCREMENT , `Name` VARCHAR(100) NOT NULL , `Uses` INT NOT NULL DEFAULT '0' , PRIMARY KEY (`Id`), UNIQUE `Id` (`Name`)) ENGINE = InnoDB;
    # INSERT INTO commandsused (Name) VALUES (%s) ON DUPLICATE KEY UPDATE Uses=Uses+1 - SQL to update table (+1 to uses value) and insert if not in table
    # update or insert record into DB
    await makeAsyncRequest('INSERT INTO commandsused (Name) VALUES (%s) ON DUPLICATE KEY UPDATE Uses=Uses+1', (name))
    # see admin_cog.py for how this data is used

# will respond for ping of the bot
@bot.event
async def on_message(msg):  # on every message
    # if we in DMs  AND it isn't our message
    if msg.guild == None and msg.author != bot.user:
        try:
            # send error message
            await msg.channel.send("Sorry you can't use this bot in DMs! You can add me to some server by this link: https://bit.ly/ARKTop")
        except BaseException as e:  # catch error
            return
        return  # ignore it we have no way to notify the user anyway
    # if content contains ping with id of our bot
    # (first case is desktop ping and second is mobile ping)
    if msg.content == f'<@!{bot.user.id}>' or msg.content == f'<@{bot.user.id}>':
        try:
            # send message and return
            await msg.channel.send(t.l['curr_prefix'].format(await get_prefix(bot, msg)))
            return
        except discord.errors.Forbidden:  # it was spaming me in DM's lol
            return
    await bot.process_commands(msg)  # if not process commands

# on error in some event
@bot.event
async def on_error(event, *args, **kwargs):
    # get tuple with exeption and traceback https://docs.python.org/3/library/sys.html#sys.exc_info
    exeption_pack = sys.exc_info()
    errors = traceback.format_exception(
        exeption_pack[0], exeption_pack[1], exeption_pack[2])
    errors_str = ''.join(errors)
    msg = f'Error happened in `{event}` event\n```{errors_str}```'
    if (msg.__len__() >= 2000):
        await sendToMe(errors_str[:1975] + '`\nEnd of first part', bot)
        await sendToMe(errors_str[1975:-1], bot, True)
        return
    else:
        await sendToMe(msg, bot, True)
        return


async def sendErrorEmbed(ctx, Id, error):
    # object to get time
    time = datetime(2000, 1, 1, 0, 0, 0, 0)
    # get config of bot
    cfg = config.Config()
    # create embed
    embed = discord.Embed()
    # paint it red
    embed.color = discord.Colour.red()
    # set title 
    embed.title = 'Opps! An error occurred!' 
    # add info
    embed.add_field(name='I notified my creator about it! A fix is already on it`s way!',
                    value=f'Your **unique** error id is `{Id}`. You can get more support in our [support](https://bit.ly/ARKDiscord) server.')
    # add bot's version 
    embed.set_footer(text=f'Bot {cfg.version}')
    # set embed's timestamp
    embed.timestamp = time.utcnow()
    # send embed 
    await ctx.send(embed=embed)

async def sendCommandNotFoundEmbed(ctx):
    # get prefix for this guild
    prefix = ctx.prefix
    # create embed
    embed = discord.Embed()
    # paint it red
    embed.color = discord.Colour.red()
    # add info
    embed.add_field(name='You entered wrong command!',
                    value=f"Command `{ctx.message.content}` doesn't exist. You can list my commands with `{prefix}help`.")
    # send embed 
    await ctx.send(embed=embed)

async def rateLimitHit(ctx, error):
    # create embed
    embed = discord.Embed()
    # paint it red
    embed.color = discord.Colour.red()
    # add title
    embed.title = 'Hold on!'
    # add info
    embed.add_field(name=f'You can only use `{ctx.message.content}` only `{error.cooldown.rate}` time(s) per `{int(error.cooldown.per)}` second(s)!',
                    value="Please try again later.")
    # send embed 
    await ctx.send(embed=embed)

async def insufficientPerms(ctx, perms):
    # add \n to each permission
    joined = '\n'.join(perms)
    # create embed
    embed = discord.Embed()
    # paint it red
    embed.color = discord.Colour.red()
    # add title
    embed.title = 'I am missing some permissions in current channel!'
    # add info
    embed.add_field(name='I need:',
                    value=f"```{joined}```")
    # send embed 
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    # get original error from d.py error
    # if none it will be set to error itself
    origError = getattr(error, "original", error)
    # get type of an error
    errorType = type(error)
    # long if elif statement 
    # if some command isn't found
    if (errorType == discord.ext.commands.errors.CommandNotFound):
        try:
            # try to send an error embed
            await sendCommandNotFoundEmbed(ctx)
            return
        # if we can't
        except discord.errors.Forbidden:
            # return
            return
    # if some check failed
    elif (errorType == discord.ext.commands.errors.CheckFailure):
        # do nothing
        # (it doesn't have any info on what has failed)
        return
    # if someone hit ratelimit
    elif (errorType == discord.ext.commands.CommandOnCooldown):
        # send an embed about it
        await rateLimitHit(ctx, error)
        return
    # if bot need some permissions
    elif (errorType == discord.ext.commands.BotMissingPermissions):
        try:
            # try to get what we are missing
            missing = error.missing_perms
        # if we can't 
        except AttributeError:
            # get it from original error
            missing = origError.missing_perms
        # n is how a permission is called in API
        # n + 1 is it's replacement for message
        map = ['manage_messages', 'Manage messages', 'external_emojis',
               'Use external emojis', 'add_reactions', 'Add reactions']
        # array with replaced permissions names
        needed = []
        # for each permission
        for perm in missing:
            # if permission is in list  
            if perm in map: 
                # put it's replacement
                needed.append(map[map.index(perm)+1])  
            # if not
            else:
                # put it as is
                needed.append(perm)  
        # send embed about it
        await insufficientPerms(ctx,needed)
        return
    # if bot is missing some permissions
    elif (errorType == discord.errors.Forbidden):
        # add some of them to the list
        needed_perms = ['Add reactions', 'Use external emojis', 'Send and read messages', 'Manage messages']
        try:
            # try to send message
            await insufficientPerms(ctx, needed_perms)
            return
        # if we can't 
        except discord.Forbidden:
            # return
            return
    # debug
    # I really need some good logging system
    debug.debug('Entered error handler')
    # format exception
    errors = traceback.format_exception(
        type(error), error, error.__traceback__)
    # get current time
    Time = int(time.time())
    # insert error record into DB
    await makeAsyncRequest('INSERT INTO errors(Error, Time, UserDiscordId, ChannelDiscordId, GuildDiscordId, Message) VALUES (%s,%s,%s,%s,%s,%s)',
    (json.dumps(errors), Time, ctx.author.id, ctx.channel.id, ctx.guild.id, ctx.message.content,))
    # select inserted error record
    data = await makeAsyncRequest('SELECT * FROM errors WHERE Time=%s', (Time,))
    # get it's id
    Id = data[0][0]
    # send error embed with this id
    await sendErrorEmbed(ctx,Id,error)
    # add each error together 
    errors_str = ''.join(errors)
    # format time
    date = datetime.utcfromtimestamp(Time).strftime('%Y-%m-%d %H:%M:%S')
    # format message for me 
    message = f'''
Error happened! 
`{errors_str}`
Error id : `{Id}`
Message : `{ctx.message.content}`
Error happened : `{date}`
Guild name : `{ctx.guild.name}`
Guild id : `{ctx.guild.id}`
    '''
    # if message has over 2k characters
    if (message.__len__() >= 2000):
        try:
            # send it in chunks
            await sendToMe(message[:1975] + '`\nEnd of first part', bot)
            await sendToMe(message[1975:-1], bot, True)
        # if we can't 
        except BaseException as e:
            await sendToMe('Lenth of error message is over 4k!', bot, True)
            await sendToMe(f'''Error id : `{Id}`
Message : `{ctx.message.content}`
When this happened : `{date}`
Guild name : `{ctx.guild.name}`
Guild id : `{ctx.guild.id}`
Error : {e}''', bot)
    else:
        await sendToMe(message, bot, True)

    
# was causing problems and was using python implementation of asyncio instead of C one (which is faster)
# nest_asyncio.apply() # patch loop https://pypi.org/project/nest-asyncio/
bot.run(conf.token)  # get our discord token and FIRE IT UP !
