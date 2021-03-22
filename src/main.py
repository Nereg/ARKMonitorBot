from charcoal import Charcoal
import classes as c # our classes
from helpers import * # our helpers
import config  # config
import discord # main discord libary
from discord.ext import commands # import commands extension
import commands as cmd # import all our commands
from menus import * # menus like selector of servers
from server_cmd import * # !server command
import json # json module
import traceback # traceback 
import time # time 
from datetime import datetime
import dbl_cog # cog with top.gg updater
import os 
import admin_cog # cog with admin commands
from discord import permissions 
from discord.ext.commands import has_permissions, CheckFailure
import updater # cog with updater of servers in DB (main consern annoying AF)
import automessage # cog with !automessage command and updater for it 
import nest_asyncio
import campfire

# classes.py - just classes for data shareing and processing
# config.py - main bot config
# commands.py - all commands live here
# helpers.py - helper funtions (like work with DB)

debug = Debuger('main') # create debuger (see helpers.py)
conf = config.Config() # load config
game = discord.Game('ping me to get prefix') # set custom status for bot (no it isn;t possible to put buttons like for user's profiles)
bot = commands.Bot(command_prefix=get_prefix,help_command=None,activity=game) # create bot with default prefix and no help command
debug.debug('Inited DB and Bot!') # debug into console !
t = c.Translation() # load default english translation

bot.loop.set_debug(conf.debug) # if conf.debug is True asyncio will output additional debug info into logs

@bot.command()
async def help(ctx):
    time = datetime(2000,1,1,0,0,0,0) # get random time 
    message = discord.Embed(title='List of commands',timestamp=time.utcnow()) # set title of embed
    prefix = await get_prefix(bot,ctx.message) # get current prefix
    isInline=False # junk from tests but still used 
    message.set_footer(text=f'Requested by {ctx.author.name} • Bot {conf.version} • GPLv3 ',icon_url=ctx.author.avatar_url) # set default footer 
    #define value for Server section
    serverValue = f'''**`{prefix}server info`- select and view info about added server
`{prefix}server add <IP>:<Query port>`- add server to your list
`{prefix}server delete`- delete server from your list
`{prefix}server alias`- list aliases for your servers
`{prefix}server alias`- list aliases for your servers
`{prefix}server alias "<Alias>"`- select and add alias for server
`{prefix}server alias delete`- delete alias for your server**'''
    message.add_field(name=f'**Server group:**',value=serverValue) # add server section to the embed
    #define value for notifications section
    notificationsValue = f'''**`{prefix}watch`- select server and bot will send a message when it goes online/offline in current channel
`{prefix}unwatch` - undone what `{prefix}watch` command do 
`{prefix}automessage #any_channel` - bot will send and update message about some server!
`{prefix}automessage` - list any automessages you have
`{prefix}automessage delete` - delete all automessages for some server
**'''
    message.add_field(name=f'**Notifications:**',value=notificationsValue,inline=isInline) # add notifications section to the embed
    miscValue =f'**`{prefix}info`- get info about this bot (e.g. support server, github etc.)**' # define misc sections value
    message.add_field(name=f'**Miscellaneous:**',value=miscValue,inline=isInline) # add misc section to the embed 
    await ctx.send(embed=message) # and send it

@bot.event
async def on_command_completion(ctx):
    name = ctx.command.name # extract name of command
    if (name == 'server'): # if it is a server command (I am too lzy to chop the into subcommands or smth like that)
        command = ctx.args[2] # get the "subcommand"
        correctCommands = ['add','info','delete','alias'] # list of valid "subcommands"
        if (command not in correctCommands): # if it isn't correct
            return # return
        else: # else
            name += ' ' + command # append name of "subcommand" to main name
    #CREATE TABLE `bot`.`commandsused` ( `Id` INT NOT NULL AUTO_INCREMENT , `Name` VARCHAR(100) NOT NULL , `Uses` INT NOT NULL DEFAULT '0' , PRIMARY KEY (`Id`), UNIQUE `Id` (`Name`)) ENGINE = InnoDB; 
    #INSERT INTO commandsused (Name) VALUES (%s) ON DUPLICATE KEY UPDATE Uses=Uses+1 - SQL to update table (+1 to uses value) and insert if not in table 
    await makeAsyncRequest('INSERT INTO commandsused (Name) VALUES (%s) ON DUPLICATE KEY UPDATE Uses=Uses+1',(name)) # update or insert record into DB
    # see admin_cog.py for how this data is used

#add all cogs
bot.add_cog(ServerCmd(bot))
bot.add_cog(cmd.BulkCommands(bot))
bot.add_cog(admin_cog.Admin(bot))
bot.add_cog(dbl_cog.TopGG(bot))
bot.add_cog(updater.Updater(bot))
bot.add_cog(automessage.Automessage(bot))
bot.add_cog(campfire.Campfire(bot))
bot.add_cog(Charcoal(bot))

# response for ping of bot
@bot.event
async def on_message(msg): # on every message 
    if msg.content == f'<@!{bot.user.id}>' or  msg.content == f'<@{bot.user.id}>': # if content contains ping with id of our bot 
        await msg.channel.send(t.l['curr_prefix'].format(await get_prefix(bot,msg))) # send message and return
        return
    await bot.process_commands(msg) # if not process commands

# !prefix command 
@commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True) # default pwrmissions check 
@bot.command()
async def prefix(ctx,*args):
    if (args.__len__() <= 0): # if no additional parameters 
        await ctx.send(t.l['curr_prefix'].format(ctx.prefix)) # send current prefix and return 
        return
    else: # if not
        Permissions = ctx.author.permissions_in(ctx.channel) # get permissions of caller in current channel 
        needed_perms =  permissions.Permissions(manage_roles=True) # set needed permissions (manage roles)
        if (needed_perms <= Permissions): # check permissions 
            prefix = args[0] # if check succseesed 
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
        else: # if check failed 
            await ctx.send('You need manage roles permission to change my prefix!') # send error message
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
async def on_error(event,*args,**kwargs): 
    exeption_pack = sys.exc_info() # get tuple with exeption and traceback https://docs.python.org/3/library/sys.html#sys.exc_info
    errors = traceback.format_exception(exeption_pack[0],exeption_pack[1],exeption_pack[2])
    errors_str = ''.join(errors)
    msg = f'Error happened in `{event}` event\n```{errors_str}```'
    if (msg.__len__() >= 2000):
        await sendToMe(f'Error message for `{event}` event is bigger that 2k!',bot)
        return
    else:
        await sendToMe(msg,bot)
        return

@bot.event
async def on_command_error(ctx,error):     
    meUser = bot.get_user(277490576159408128)
    meDM = await meUser.create_dm()
    origError = getattr(error, "original", error)
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
    if (type(error) == discord.ext.commands.BotMissingPermissions or type(origError) ==  discord.ext.commands.BotMissingPermissions):
        try:
            missing = error.missing_perms # to not type l  o  n  g name 
        except AttributeError: # TODO test this
            missing = origError.missing_perms
        map = ['manage_messages','Manage messages','external_emojis','Use external emojis','add_reactions', 'Add reactions'] # replacement list
        needed = [] # replaced list
        for perm in missing: # for each permission
            if perm in map: # if permission is in list
                needed.append(map[map.index(perm)+1]) # put it's replacement 
            else:
                needed.append(perm) # if not put it as is
        # and send message
        await ctx.send(f"Bot can't work in current channel without those permissions: `{' , '.join(needed)}`. Please check if bot have this permissions in current channel and try again.")
        return
    if (type(error) == discord.errors.Forbidden or type(origError) == discord.errors.Forbidden):
        needed_perms = "```Add reactions\nUse external emojis\nSend and read messages\nManage messages```"
        try:
            await ctx.send(f'Hey! Bot is missing some permissions! Bot needs:\n{needed_perms}')
        except discord.Forbidden:
            try:
                await ctx.author.send(f'Hey hello. You invited me to your `{ctx.guild.name}` guild and used `{ctx.message.content}` command. But I am missing some permissions! Most likely some channel permissions overrides bots one. I need:\n{needed_perms}')
            except BaseException:
                return
        return
    debug.debug('Entered error handler') 
    errors = traceback.format_exception(type(error), error, error.__traceback__)
    Time = int(time.time())
    await makeAsyncRequest('INSERT INTO errors(Error, Time, UserDiscordId, ChannelDiscordId, GuildDiscordId, Message) VALUES (%s,%s,%s,%s,%s,%s)',(json.dumps(errors),Time,ctx.author.id,ctx.channel.id,ctx.guild.id,ctx.message.content,))
    debug.debug('Made SQL')
    data = await makeAsyncRequest('SELECT * FROM errors WHERE Time=%s',(Time,))
    Id = data[0][0]
    meUser = bot.get_user(277490576159408128)
    await ctx.send(f'Error occured ! I logged in and notified my creator. Your unique error id is `{Id}`. You can message my creator {meUser.name}#{meUser.discriminator} or report this error to my support discord server ! You can join it by this link : <https://bit.ly/ARKDiscord>')
    debug.debug('Sent channel message')
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
Айди гильдии: `{ctx.guild.id}`
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
@commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True)
async def test(ctx):
    selector = Selector(ctx,bot,c.Translation())
    server = await selector.select()
    if server == '':
        return
    print(server.name)
    await ctx.send(await server.getBattlemetricsUrl(server))
    
nest_asyncio.apply() # patch loop https://pypi.org/project/nest-asyncio/
bot.run(conf.token) # get our discord token and FIRE IT UP !