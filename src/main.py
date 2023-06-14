# from charcoal import Charcoal
# import cogs.utils.classes as c  # our classes
# from server_cmd import *  # !server command
import json  # json module
import time  # time
import traceback  # traceback
import typing
from datetime import datetime
from pathlib import Path
from typing import Optional

import config  # config
import discord  # main discord library
from discord import MemberCacheFlags, permissions
from discord.ext import commands  # import commands extension
from discord.ext.commands import (
    CheckFailure,
    Context,
    Greedy,
    HybridCommand,
    has_permissions,
)

from cogs.utils.helpers import *  # our helpers

# classes.py - just classes for data shareing and processing
# config.py - main bot config
# commands.py - all commands live here
# helpers.py - helper functions (like work with DB)

debug = Debuger("main")  # create debugger (see helpers.py)
conf = config.Config()  # load config
# set custom status for bot (sadly it isn't possible to put buttons like in user's profiles)
game = discord.Game("slash commands! Ping me to learn more")
intents = discord.Intents(messages=True, guilds=True, reactions=True)
# create auto sharded bot with default prefix and no help command
bot = commands.AutoShardedBot(
    intents=intents,
    command_prefix=get_prefix,
    help_command=None,
    activity=game,
    strip_after_prefix=True,
    member_cache_flags=MemberCacheFlags.none(),
)
bot.cfg = conf
debug.debug("Inited DB and Bot!")  # debug into console !
t = c.Translation()  # load default english translation


# setup function
async def setup():
    print("Started loading cogs")
    # search for cogs
    cogs = [p.stem for p in Path(".").glob("./src/cogs/*_cog.py")]
    print(cogs)
    for cog in cogs:
        # print(f"cogs.{cog}")
        await bot.load_extension(f"cogs.{cog}")
        print(f"{cog} cog loaded")
    # load jishaku
    await bot.load_extension("jishaku")
    # hide it's command
    bot.get_command("jsk").hidden = True
    print("Finished setup function")


# ~~~~~~~~~~~~~~~~~~~~~
#       COMMANDS
# ~~~~~~~~~~~~~~~~~~~~~
@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
    ctx: Context,
    guilds: Greedy[discord.Object],
    spec: Optional[typing.Literal["~", "*", "^"]] = None,
) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException as e:
            await ctx.send(e)
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


@bot.hybrid_command(description="Need help with the bot? This is the right command!")
async def help(ctx):
    time = datetime(2000, 1, 1, 0, 0, 0, 0)  # get time object
    # set title and timestamp of embed
    message = discord.Embed(title="List of commands", timestamp=time.utcnow())
    # get current prefix
    prefix = ctx.prefix
    # set footer for embed
    message.set_footer(
        text=f"Requested by {ctx.author.name} • Bot {conf.version} • GPLv3 ",
        icon_url=ctx.author.display_avatar.url,
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
`{prefix}automessage add #any_channel` - Bot will send and update message about a server!
`{prefix}automessage list` - List any automessages you have
`{prefix}automessage delete` - Delete **all** automessages for a server
**"""
    # add notifications section to the embed
    message.add_field(
        name=f"**Notification commands:**", value=notificationsValue, inline=False
    )
    # define misc sections value
    miscValue = f"**`{prefix}info`- Get info about this bot (e.g. support server, GitHub etc.)**"
    # add misc section to the embed
    message.add_field(
        name=f"**Miscellaneous Commands:**", value=miscValue, inline=False
    )
    # and send it
    await ctx.send(embed=message)


# ~~~~~~~~~~~~~~~~~~~~~
#        EVENTS
# ~~~~~~~~~~~~~~~~~~~~~


# will respond for ping of the bot
@bot.event
async def on_message(msg):  # on every message
    # await bot.process_commands(msg)
    # return
    # if we in DMs  AND it isn't our message
    if msg.guild == None and msg.author != bot.user:
        try:
            # send error message

            await msg.channel.send(
                "Sorry you can't use this bot in DMs! You can add me to a server by this link: https://bit.ly/ARKTop"
            )
        except BaseException as e:  # catch error
            return
        return  # ignore it we have no way to notify the user anyway
    # if content starts with ping with id of our bot
    # (first case is desktop ping and second is mobile ping)
    if msg.content.startswith(f"<@!{bot.user.id}>") or msg.content.startswith(
        f"<@{bot.user.id}>"
    ):
        try:
            embed = discord.Embed(title="Slash commands!", color=randomColor())
            embed.add_field(
                name="This bot now supports only slash commands!",
                value="If you don't know how to use them just assume the the prefix now is `/` and find the bot there!",
            )
            # send message and return
            await msg.channel.send(embed=embed)
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
    embed.title = "I am missing some permissions in this channel!"
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
    embed.title = "That channel could not be found!"
    # add info
    embed.add_field(
        name=f"Channel with id `{error.argument[2:-1]}` isn't found!",
        value="Maybe you copied this channel from another server? ",
    )
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
    # if required parameter is missing
    elif errorType == discord.ext.commands.errors.MissingRequiredArgument:
        embed = discord.Embed(
            title="Required parameter is missing!", color=discord.Color.red()
        )
        embed.add_field(
            name=f"Parameter `{error.param.name}` is required!", value="\u200B"
        )
        await ctx.send(embed=embed)
        return
    # debug
    # I really need some good logging system
    debug.debug("Entered error handler")
    # format exception
    errors = traceback.format_exception(type(error), error, error.__traceback__)
    # get current time
    Time = int(time.time())
    # insert error record into DB
    # await makeAsyncRequest(
    #     "INSERT INTO errors(Error, Time, UserDiscordId, ChannelDiscordId, GuildDiscordId, Message) VALUES (%s,%s,%s,%s,%s,%s)",
    #     (
    #         json.dumps(errors),
    #         Time,
    #         ctx.author.id,
    #         ctx.channel.id,
    #         ctx.guild.id,
    #         ctx.message.content,
    #     ),
    # )
    # select inserted error record
    # data = await makeAsyncRequest("SELECT * FROM errors WHERE Time=%s", (Time,))
    # # get it's id
    # Id = data[0][0]
    # send error embed with this id
    # await sendErrorEmbed(ctx, Id, error)
    # add each error together
    errors_str = "".join(errors)
    # format time
    date = datetime.utcfromtimestamp(Time).strftime("%Y-%m-%d %H:%M:%S")
    # format message for me
    message = f"""
Error happened! 
`{errors_str}`
Error id : `{0}`
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
                f"""Error id : `{0}`
Message : `{ctx.message.content}`
When this happened : `{date}`
Guild name : `{ctx.guild.name}`
Guild id : `{ctx.guild.id}`
Error : {e}""",
                bot,
            )
    else:
        await sendToMe(message, bot, True)


async def main():
    async with bot:
        await setup()
        # await bot.tree.sync(guild=discord.Object(id=349178138258833418))
        # if conf.debug is True asyncio will output additional debug info into logs
        bot.loop.set_debug(conf.debug)
        await bot.start(conf.token)


# was causing problems and was using python implementation of asyncio instead of C one (which is faster)
# nest_asyncio.apply() # patch loop https://pypi.org/project/nest-asyncio/
# bot.run(conf.token)  # get our discord token and FIRE IT UP !
asyncio.run(main())
