import cogs.utils.classes as c  # our classes
from cogs.utils.helpers import *  # our helpers
import config  # config
import discord  # main discord library
from discord.ext import commands  # import commands extension
from cogs.utils.menus import *  # menus like selector of servers
import json  # json module
import traceback  # traceback
import time  # time
from datetime import datetime
from discord import permissions
from discord.ext.commands import has_permissions, CheckFailure
from pathlib import Path

# classes.py - just classes for data shareing and processing
# config.py - main bot config
# commands.py - all commands live here
# helpers.py - helper functions (like work with DB)

debug = Debuger("main")  # create debugger (see helpers.py)
conf = config.Config()  # load config
# set custom status for bot (sadly it isn't possible to put buttons like in user's profiles)
game = discord.Game("ping me to get prefix")
# create auto sharded bot with default prefix and no help command
bot = commands.AutoShardedBot(
    command_prefix=get_prefix, help_command=None, activity=game
)
bot.cfg = conf
bot.myCogs = []
debug.debug("Initted DB and Bot!")  # debug into console !
t = c.Translation()  # load default english translation

# if conf.debug is True asyncio will output additional debug info into logs
bot.loop.set_debug(conf.debug)

# setup function
def setup():
    print("Started loading cogs")
    # search for cogs
    cogs = [p.stem for p in Path(".").glob("./src/cogs/*.py")]
    print(cogs)
    for cog in cogs:
        print(f"cogs.{cog}")
        bot.load_extension(f"cogs.{cog}")
        print(f"{cog} cog loaded")
    print("Finished loading cogs")


# ~~~~~~~~~~~~~~~~~~~~~
#       COMMANDS
# ~~~~~~~~~~~~~~~~~~~~~

# !prefix command
# default permissions check
@commands.bot_has_permissions(
    add_reactions=True,
    read_messages=True,
    send_messages=True,
    manage_messages=True,
    external_emojis=True,
)
@bot.command()
async def prefix(ctx, *args):
    if args.__len__() <= 0:  # if no additional parameters
        # send current prefix and return
        await ctx.send(t.l["curr_prefix"].format(ctx.prefix))
        return
    else:  # if not
        # get permissions of caller in current channel
        permissions = ctx.channel.permissions_for(ctx.author)
        # set needed permissions (manage roles)
        needed_perms = discord.Permissions(manage_roles=True)
        if needed_perms <= permissions:  # check permissions
            # if check successes
            # get new prefix from params
            prefix = args[0]
            # if @ in prefix
            if "@" in prefix:
                # send error message
                await ctx.send("You can`t set prefix that contains @!")
                return
            # get settings for current guild
            data = await makeAsyncRequest(
                "SELECT * FROM settings WHERE GuildId = %s", (ctx.guild.id,)
            )
            # if we have record for current guild
            if data.__len__() > 0:
                # update it
                await makeAsyncRequest(
                    "UPDATE settings SET Prefix=%s WHERE GuildId=%s",
                    (
                        prefix,
                        ctx.guild.id,
                    ),
                )
            # else
            else:
                # create one
                await makeAsyncRequest(
                    "INSERT INTO settings (GuildId,Prefix,Type) VALUES (%s,%s,0)",
                    (
                        ctx.guild.id,
                        prefix,
                    ),
                )
            # send done message
            await ctx.send(t.l["done"])
        # if check failed
        else:
            # send error message
            await ctx.send("You need manage roles permission to change my prefix!")
            return


# main help command
@bot.command()
async def help(ctx):
    time = datetime(2000, 1, 1, 0, 0, 0, 0)  # get time object
    # set title and timestamp of embed
    message = discord.Embed(title="List of commands", timestamp=time.utcnow())
    # get current prefix
    prefix = ctx.prefix
    # set footer for embed
    message.set_footer(
        text=f"Requested by {ctx.author.name} • Bot {conf.version} • GPLv3 ",
        icon_url=ctx.author.display_avatar,
    )
    # define value for Server section
    serverValue = f"""**`{prefix}server info`- View info about added server
`{prefix}server add <IP>:<Query port>`- Add server (Steam only, both official and not) to your list
`{prefix}server delete`- Delete server from your list
`{prefix}server alias`- List aliases for your servers
`{prefix}server alias "<Alias>"`- Add alias for a server
`{prefix}server alias delete`- Delete alias for your server**"""
    # add server section to the embed
    message.add_field(name=f"**Server commands:**", value=serverValue)
    # define value for notifications section
    notificationsValue = f"""**`{prefix}watch`- Bot will send a message when selected server goes online/offline in current channel
`{prefix}unwatch` - Stop watching server
`{prefix}automessage #any_channel` - Bot will send and update message about a server!
`{prefix}automessage` - List any automessages you have
`{prefix}automessage delete` - Delete **all** automessages for a server
**"""
    # add notifications section to the embed
    message.add_field(
        name=f"**Notification commands:**", value=notificationsValue, inline=False
    )
    # define misc sections value
    miscValue = f"**`{prefix}info`- Get info about this bot (e.g. support server, GitHub etc.)**"
    # add misc section to the embed
    message.add_field(name=f'**Miscellaneous Commands:**', value=miscValue,
                      inline=False)
    # and send it  
    await ctx.send(embed=message)  


# some old command
@bot.command()
async def share(ctx):
    await ctx.send(t.l["share_msg"].format(conf.inviteUrl))


# ~~~~~~~~~~~~~~~~~~~~~
#        EVENTS
# ~~~~~~~~~~~~~~~~~~~~~

# used to count executed commands
# doesn't work at all
@bot.event
async def on_command_completion(ctx):
    name = ctx.command.name  # extract name of command
    if (
        name == "server"
    ):  # if it is a server command (I am too lazy to chop the into subcommands or smth like that)
        try:
            command = ctx.args[2]  # get the "subcommand"
        except IndexError:  # that happens if we write just //server
            return
        correctCommands = [
            "add",
            "info",
            "delete",
            "alias",
        ]  # list of valid "subcommands"
        if command not in correctCommands:  # if it isn't correct
            return  # return
        else:  # else
            name += " " + command  # append name of "subcommand" to main name
    # CREATE TABLE `bot`.`commandsused` ( `Id` INT NOT NULL AUTO_INCREMENT , `Name` VARCHAR(100) NOT NULL , `Uses` INT NOT NULL DEFAULT '0' , PRIMARY KEY (`Id`), UNIQUE `Id` (`Name`)) ENGINE = InnoDB;
    # INSERT INTO commandsused (Name) VALUES (%s) ON DUPLICATE KEY UPDATE Uses=Uses+1 - SQL to update table (+1 to uses value) and insert if not in table
    # update or insert record into DB
    await makeAsyncRequest(
        "INSERT INTO commandsused (Name) VALUES (%s) ON DUPLICATE KEY UPDATE Uses=Uses+1",
        (name),
    )
    # see admin_cog.py for how this data is used


# will respond for ping of the bot
@bot.event
async def on_message(msg):  # on every message
    # if we in DMs  AND it isn't our message
    if msg.guild == None and msg.author != bot.user:
        try:
            # send error message

            await msg.channel.send(
                "Sorry you can't use this bot in DMs! You can add me to some server by this link: https://bit.ly/ARKTop"
            )
        except BaseException as e:  # catch error
            return
        return  # ignore it we have no way to notify the user anyway
    # if content contains ping with id of our bot
    # (first case is desktop ping and second is mobile ping)
    if msg.content == f"<@!{bot.user.id}>" or msg.content == f"<@{bot.user.id}>":
        try:
            # send message and return
            await msg.channel.send(
                t.l["curr_prefix"].format(await get_prefix(bot, msg))
            )
            return
        except discord.errors.Forbidden:  # it was spaming me in DM's lol
            return
    await bot.process_commands(msg)  # if not process commands


# on error in some event
@bot.event
async def on_error(event, *args, **kwargs):
    # get tuple with exception and traceback https://docs.python.org/3/library/sys.html#sys.exc_info
    exception_pack = sys.exc_info()
    errors = traceback.format_exception(
        exception_pack[0], exception_pack[1], exception_pack[2]
    )
    errors_str = "".join(errors)
    msg = f"Error happened in `{event}` event\n```{errors_str}```"
    if msg.__len__() >= 2000:
        await sendToMe(errors_str[:1975] + "`\nEnd of first part", bot)
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
    embed.title = "Opps! An error occurred!"
    # add info
    embed.add_field(
        name="I notified my creator about it! A fix is already on it's way!",
        value=f"Your **unique** error id is `{Id}`. You can get more support in our [support](https://bit.ly/ARKDiscord) server.",
    )
    # add bot's version
    embed.set_footer(text=f"Bot {cfg.version}")
    # set embed's timestamp
    embed.timestamp = time.utcnow()
    try:
        # send embed
        await ctx.send(embed=embed)
    except:
        return


async def sendCommandNotFoundEmbed(ctx):
    # get prefix for this guild
    prefix = ctx.prefix
    # create embed
    embed = discord.Embed()
    # paint it red
    embed.color = discord.Colour.red()
    # add info
    embed.add_field(
        name="You entered wrong command!",
        value=f"Command `{ctx.message.content}` doesn't exist. You can list my commands with `{prefix}help`.",
    )
    # send embed
    await ctx.send(embed=embed)


async def rateLimitHit(ctx, error):
    # create embed
    embed = discord.Embed()
    # paint it red
    embed.color = discord.Colour.red()
    # add title
    embed.title = "Hold on!"
    # add info
    embed.add_field(
        name=f"You can only use `{ctx.message.content}` only `{error.cooldown.rate}` time(s) per `{int(error.cooldown.per)}` second(s)!",
        value="Please try again later.",
    )
    # send embed
    await ctx.send(embed=embed)


async def insufficientPerms(ctx, perms):
    # add \n to each permission
    joined = "\n".join(perms)
    # create embed
    embed = discord.Embed()
    # paint it red
    embed.color = discord.Colour.red()
    # add title
    embed.title = 'I am missing some permissions in this channel!'
    # add info
    embed.add_field(name="I need:", value=f"```{joined}```")
    # send embed
    await ctx.send(embed=embed)


async def channelNotFound(ctx, error):
    # create embed
    embed = discord.Embed()
    # paint it red
    embed.color = discord.Colour.red()
    # add title
    embed.title = 'That channel could not be found!'
    # add info
    embed.add_field(name=f"Channel with id `{error.argument[2:-1]}` isn't found!",
                    value="Maybe you copied this channel from another server? ")
    # send embed 
    await ctx.send(embed=embed)


@bot.check
async def check_commands(ctx):
    if getattr(conf, "deprecation", True):
        embed = discord.Embed()
        embed.title = "Notice!"
        embed.colour = discord.Colour.red()
        embed.add_field(
            name="Regular commands will stop working in <t:1634294539:R>!",
            value="Instead there will be new slash commands.",
        )
        embed.add_field(
            name="To check if you are ready for the change use `validateSlash` command.",
            value="No data will be lost after the transition!",
        )
        await ctx.send(embed=embed)
    return True


@bot.event
async def on_command_error(ctx, error):
    # get original error from d.py error
    # if none it will be set to error itself
    origError = getattr(error, "original", error)
    # get type of an error
    errorType = type(error)
    # long if elif statement
    # if some command isn't found
    if errorType == discord.ext.commands.errors.CommandNotFound:
        try:
            # try to send an error embed
            await sendCommandNotFoundEmbed(ctx)
            return
        # if we can't
        except discord.errors.Forbidden:
            # return
            return
    # if some channel isn't found
    if errorType == discord.ext.commands.errors.ChannelNotFound:
        await channelNotFound(ctx, error)
        return
    # if some check failed
    elif errorType == discord.ext.commands.errors.CheckFailure:
        # do nothing
        # (it doesn't have any info on what has failed)
        return
    # if someone hit ratelimit
    elif errorType == discord.ext.commands.CommandOnCooldown:
        # send an embed about it
        await rateLimitHit(ctx, error)
        return
    # if bot need some permissions
    elif errorType == discord.ext.commands.BotMissingPermissions:
        try:
            # try to get what we are missing
            missing = error.missing_permissions
        # if we can't
        except AttributeError:
            # get it from original error
            missing = origError.missing_permissions
        # n is how a permission is called in API
        # n + 1 is it's replacement for message
        map = [
            "manage_messages",
            "Manage messages",
            "external_emojis",
            "Use external emojis",
            "add_reactions",
            "Add reactions",
        ]
        # array with replaced permissions names
        needed = []
        # for each permission
        for perm in missing:
            # if permission is in list
            if perm in map:
                # put it's replacement
                needed.append(map[map.index(perm) + 1])
            # if not
            else:
                # put it as is
                needed.append(perm)
        # send embed about it
        await insufficientPerms(ctx, needed)
        return
    # if bot is missing some permissions
    elif errorType == discord.errors.Forbidden:
        # add some of them to the list
        needed_perms = [
            "Add reactions",
            "Use external emojis",
            "Send and read messages",
            "Manage messages",
        ]
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
    debug.debug("Entered error handler")
    # format exception
    errors = traceback.format_exception(type(error), error, error.__traceback__)
    # get current time
    Time = int(time.time())
    # insert error record into DB
    await makeAsyncRequest(
        "INSERT INTO errors(Error, Time, UserDiscordId, ChannelDiscordId, GuildDiscordId, Message) VALUES (%s,%s,%s,%s,%s,%s)",
        (
            json.dumps(errors),
            Time,
            ctx.author.id,
            ctx.channel.id,
            ctx.guild.id,
            ctx.message.content,
        ),
    )
    # select inserted error record
    data = await makeAsyncRequest("SELECT * FROM errors WHERE Time=%s", (Time,))
    # get it's id
    Id = data[0][0]
    # send error embed with this id
    await sendErrorEmbed(ctx, Id, error)
    # add each error together
    errors_str = "".join(errors)
    # format time
    date = datetime.utcfromtimestamp(Time).strftime("%Y-%m-%d %H:%M:%S")
    # format message for me
    message = f"""
Error happened! 
`{errors_str}`
Error id : `{Id}`
Message : `{ctx.message.content}`
Error happened : `{date}`
Guild name : `{ctx.guild.name}`
Guild id : `{ctx.guild.id}`
    """
    # if message has over 2k characters
    if message.__len__() >= 2000:
        try:
            # send it in chunks
            await sendToMe(message[:1975] + "`\nEnd of first part", bot)
            await sendToMe(message[1975:-1], bot, True)
        # if we can't
        except BaseException as e:
            await sendToMe("Lenth of error message is over 4k!", bot, True)
            await sendToMe(
                f"""Error id : `{Id}`
Message : `{ctx.message.content}`
When this happened : `{date}`
Guild name : `{ctx.guild.name}`
Guild id : `{ctx.guild.id}`
Error : {e}""",
                bot,
            )
    else:
        await sendToMe(message, bot, True)


setup()
# was causing problems and was using python implementation of asyncio instead of C one (which is faster)
# nest_asyncio.apply() # patch loop https://pypi.org/project/nest-asyncio/
bot.run(conf.token)  # get our discord token and FIRE IT UP !
