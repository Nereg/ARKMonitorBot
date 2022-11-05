from cogs.utils.helpers import *
import cogs.utils.classes as c
from cogs.utils.menus import *
import discord  # main discord library
from discord.ext import commands  # import commands extension
import json
import aiohttp
import cogs.utils.classes as c
import a2s
import time
from discord.ext import commands
import typing
from discord import app_commands

class ServerCmd(commands.Cog):
    def __init__(self, bot):
        self.cfg = config.Config()
        self.bot = bot

    async def serverInfo(self, serverRecord, ctx):
        # get list of player from server record
        playersList = c.PlayersList.fromJSON(serverRecord[5])
        # get server object from server record
        server = c.ARKServer.fromJSON(serverRecord[4])
        # get online status of the server from server record
        online = bool(serverRecord[6])
        # get object to get time
        time = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        # get list of players
        playersList = playersList.list
        # get alias for server
        aliases = await getAlias(serverRecord[0], ctx.guild.id)
        # if we have no alias set name to original server name
        # else set it to the alias
        name = server.name if aliases == "" else aliases
        # get more info about server from server record
        moreinfo = json.loads(serverRecord[8])
        # if we have battleUrl in moreinfo set battleUrl to it
        # else set battleUrl to empty
        battleUrl = moreinfo["battleUrl"] if "battleUrl" in moreinfo else ""
        # variable for players
        playersValue = ""
        # variable for time of players
        timeValue = ""
        # pick random color for embed
        color = randomColor()
        # for each player in player list
        for player in playersList:
            # add it's name to value
            playersValue += player.name + "\n"
            # and how much time it played
            timeValue += player.time + "\n"
        # if server is offline or there is no players on it
        if not online or server.online == 0 or len(playersList) <= 0:
            # set defaults
            playersValue = "No one is on the server"
            timeValue = "\u200B"
        # if server is online set variable to green circle
        # else set it to red circle
        status = ":green_circle:" if online else ":red_circle:"
        # make first embed
        emb1 = discord.Embed(title=name + " " + status, url=battleUrl, color=color)
        emb1.add_field(name="Name", value=playersValue)
        emb1.add_field(name="Time played", value=timeValue)
        # if server offline override online players count
        server.online = server.online if online else 0
        emb2 = discord.Embed(color=color, timestamp=time.utcnow())  # second embed
        emb2.set_footer(
            text=f"Requested by {ctx.author.name} • Bot {self.cfg.version}",
            icon_url=ctx.author.display_avatar,
        )
        emb2.add_field(name="IP:", value=server.ip)
        emb2.add_field(name="Players:", value=f"{server.online}/{server.maxPlayers}")
        emb2.add_field(name="Map:", value=server.map)
        emb2.add_field(name="Ping:", value=f"{server.ping} ms.")
        await ctx.send(embeds=[emb1, emb2])

    # @commands.bot_has_permissions(
    #     add_reactions=True,
    #     read_messages=True,
    #     send_messages=True,
    #     manage_messages=True,
    #     external_emojis=True,
    # )
    @commands.hybrid_group(
        invoke_without_command=True,
        case_insensitive=True,
        brief="Base command for many features of the bot",
    )
    @commands.cooldown(10, 60, type=commands.BucketType.user)
    async def server(self, ctx):
        embed = discord.Embed(title="No subcommand selected!")
        embed.add_field(
            name="Possible subcommands:", value="```\nadd\ndelete\ninfo\nalias```"
        )
        embed.add_field(
            name="Example of `add` subcommand:", value=f"`{ctx.prefix}server add`"
        )
        await ctx.send(embed=embed)


    @server.command(description="Add an ARK server to your list")
    @app_commands.describe(server_ip='IP:Port of a server you want to add')
    async def add(
        self,
        ctx,
        server_ip: typing.Optional[str],
    ) -> None:
        # if ip isn't correct
        if not IpCheck(server_ip):
            # crete embed
            embed = discord.Embed(
                color=discord.Colour.red(), title="Something is wring with ip!"
            )
            # and send it
            await ctx.send(embed=embed)
            return
        
        # get any servers with such ip
        servers = await makeAsyncRequest(
            "SELECT Id FROM servers WHERE Ip=%s", (server_ip,)
        )
        # if server is already in DB
        if servers.__len__() > 0:
            # get it's ID from DB
            id = servers[0][0]
        # else
        else:
            # try to add server
            id = await AddServer(server_ip, ctx)
            # if it wasn't added
            if id is None:
                return
        
        # get added servers from server settings
        added_servers = await makeAsyncRequest(
            "SELECT ServersId FROM settings WHERE GuildId=%s", (ctx.guild.id,)
        )
        # if no record is found
        if added_servers == ():
            # create one
            await makeAsyncRequest(
                "INSERT INTO settings (GuildId,Prefix,Type) VALUES (%s,%s,0)",
                (
                    ctx.guild.id,
                    ctx.prefix,
                ),
            )
        # if list isn't empty and record is found and it contains needed data
        if len(added_servers) > 0 and added_servers != () and added_servers != ((None,),):
            # load added servers
            added_servers = json.loads(added_servers[0][0])
            # if server is already added
            if id in added_servers:
                # create
                embed = discord.Embed(
                    title="Server already added!", color=discord.Color.red()
                )
                # and send embed
                await ctx.send(embed=embed)
                return
            # if not
            else:
                # update server list
                updated_servers = added_servers + [id]
        else:
            # create server list
            updated_servers = [id]
        # update settings
        await makeAsyncRequest(
            "UPDATE settings SET ServersId = %s WHERE GuildId=%s",
            (json.dumps(updated_servers), ctx.guild.id),
        )
        # create
        embed = discord.Embed(title="Done!", color=discord.Color.green())
        # and send embed
        await ctx.send(embed=embed)

    @server.command(description="Get info about an ARK server")
    async def info(self, ctx) -> None:
        selector = Selector(ctx, ctx.bot, c.Translation())
        server = await selector.select()
        if server == "":
            return
        # else get ip
        ip = server.ip
        # get server by ip
        servers = await makeAsyncRequest("SELECT * FROM servers WHERE Ip=%s", (ip,))
        # get first match
        server = servers[0]
        # send server info
        await self.serverInfo(server, ctx)

    @server.command(description="Delete an ARK server from your list")
    async def delete(self, ctx) -> None:
        # create selector class
        selector = Selector(ctx, ctx.bot, c.Translation())
        # let the user select
        server = await selector.select()
        # if nothing was selected
        if server == "":
            # return
            return
        # else get ip
        ip = server.ip
        # get server id by ip
        server_id = await makeAsyncRequest("SELECT Id FROM servers WHERE Ip=%s", (ip,))
        server_id = server_id[0][0]
        # get guild settings
        settings = await makeAsyncRequest(
            "SELECT ServersId FROM settings WHERE GuildId=%s", (ctx.guild.id,)
        )
        # load array of server id's
        servers = json.loads(settings[0][0])
        # remove server id from list
        servers.remove(server_id)
        # update record in DB
        await makeAsyncRequest(
            "UPDATE settings SET ServersId=%s WHERE GuildId=%s",
            (
                json.dumps(servers),
                ctx.guild.id,
            ),
        )
        # get guild notifications
        notifications = await makeAsyncRequest(
            "SELECT Id, ServersIds FROM notifications WHERE GuildId=%s", (ctx.guild.id,)
        )
        # for each notification
        for notification in notifications:
            # load servers ids
            notif_servers = json.loads(notification[1])
            # if current server id is in list of servers
            if server_id in notif_servers:
                # remove it from list
                notif_servers.remove(server_id)
                # and update DB
                await makeAsyncRequest(
                    "UPDATE notifications SET ServersIds=%s WHERE Id=%s",
                    (
                        json.dumps(notif_servers),
                        notification[0],
                    ),
                )
        # delete all auto messages from DB with current guild id and server id
        await makeAsyncRequest(
            "DELETE FROM automessages WHERE ServerId = %s AND DiscordGuildId = %s",
            (
                server_id,
                ctx.guild.id,
            ),
        )
        # create embed
        embed = discord.Embed(title="Done!", color=discord.Color.green())
        # and send it
        await ctx.send(embed=embed)

    @server.group(
        description="Base command for server aliases",
        invoke_without_command=True,
        case_insensitive=True,
    )
    async def alias(self, ctx) -> None:
        embed = discord.Embed(title="No subcommand selected!")
        embed.add_field(name="Possible subcommands:", value="```\nadd\ndelete\nlist```")
        embed.add_field(
            name="Example of `add` subcommand:", value=f"`{ctx.prefix}server alias add`"
        )
        await ctx.send(embed=embed)

    @alias.command(description="Add an alias for your ARK server", name="add")
    @app_commands.describe(alias='Alias to assign to a server')
    async def add_alias(
        self,
        ctx,
        alias: typing.Optional[str],
    ) -> None:
        # create selector
        selector = Selector(ctx, ctx.bot, c.Translation())
        # and present selector
        server_obj = await selector.select()
        # if nothing was selected
        if server_obj == "":
            # return
            return
        # else get ip
        ip = server_obj.ip
        # get server id by ip
        server_id = await makeAsyncRequest("SELECT Id FROM servers WHERE Ip=%s", (ip,))
        server_id = server_id[0][0]
        # get guild aliases
        aliases = await makeAsyncRequest(
            "SELECT Aliases FROM settings WHERE GuildId=%s", (ctx.guild.id,)
        )
        # if we have some aliases
        if aliases[0][0] != "[]" and aliases[0][0] is not None:
            # load all aliases
            aliases_dec = json.loads(aliases[0][0])
            # if aliases for this server already exist
            if server_id in aliases_dec:
                # get index of the server in the list
                server_index = aliases_dec.index(server_id)
                # record old alias
                old_alias = aliases_dec[server_index + 1]
                # change existing alias
                aliases_dec[server_index + 1] = alias
                # create embed
                embed = discord.Embed(title="Done!", color=discord.Color.green())
                # add field
                embed.add_field(
                    name=f"Changed alias for `{server_obj.name}`",
                    value=f"from `{old_alias}` to `{alias}`",
                )
            # if we need to add it
            else:
                # add server id
                aliases_dec.append(server_id)
                # add alias itself
                aliases_dec.append(alias)
                # create embed
                embed = discord.Embed(title="Done!", color=discord.Color.green())
                # add field
                embed.add_field(
                    name=f"Added alias for `{server_obj.name}`",
                    value=f"New alias is `{alias}`",
                )
        # if we have no aliases
        else:
            # create alias record
            aliases_dec = [server_id, alias]
            # create embed
            embed = discord.Embed(title="Done!", color=discord.Color.green())
            # add field
            embed.add_field(
                name=f"Added alias for `{server_obj.name}`",
                value=f"New alias is `{alias}`",
            )
        await makeAsyncRequest(
            "UPDATE settings SET Aliases=%s WHERE GuildId=%s",
            (json.dumps(aliases_dec), ctx.guild.id),
        )
        await ctx.send(embed=embed)

    @alias.command(description="Delete an alias for your ARK server", name="delete")
    async def delete_alias(self, ctx) -> None:
        # create selector
        selector = Selector(ctx, ctx.bot, c.Translation())
        # and present selector
        server_obj = await selector.select()
        # if nothing was selected
        if server_obj == "":
            # return
            return
        # else get ip
        ip = server_obj.ip
        # get server id by ip
        server_id = await makeAsyncRequest("SELECT Id FROM servers WHERE Ip=%s", (ip,))
        server_id = server_id[0][0]
        # get guild aliases
        aliases = await makeAsyncRequest(
            "SELECT Aliases FROM settings WHERE GuildId=%s", (ctx.guild.id,)
        )
        # if we have some aliases
        if aliases[0][0] != "[]" and aliases[0][0] is not None:
            # load them
            aliases_dec = json.loads(aliases[0][0])
            # if we have alias for current server
            if server_id in aliases_dec:
                # get server index
                server_index = aliases_dec.index(server_id)
                # record old alias
                old_alias = aliases_dec[server_index + 1]
                # remove server id from records
                aliases_dec.pop(server_index)
                # now the alias itself is at server id position so remove it
                aliases_dec.pop(server_index)
                # update DB
                await makeAsyncRequest(
                    "UPDATE settings SET Aliases=%s WHERE GuildId=%s",
                    (json.dumps(aliases_dec), ctx.guild.id),
                )
                # create embed
                embed = discord.Embed(title="Done!", color=discord.Color.green())
                # add field to it
                embed.add_field(
                    name=f"Removed alias `{old_alias}` for",
                    value=f"`{server_obj.name}`",
                )
                # send it
                await ctx.send(embed=embed)
                return
            # if we don't
            else:
                # create embed
                embed = discord.Embed(
                    title="You have no alias for this server!",
                    color=discord.Color.red(),
                )
                # send it
                await ctx.send(embed=embed)
                return
        else:
            # create embed
            embed = discord.Embed(
                title="You have no alias for this server!",
                color=discord.Color.red(),
            )
            # send it
            await ctx.send(embed=embed)
            return

    @alias.command(description="List aliases for your ARK servers")
    async def list(self, ctx) -> None:
        # get aliases from DB
        aliases = await makeAsyncRequest(
            "SELECT Aliases FROM settings WHERE GuildId = %s", (ctx.guild.id,)
        )
        # if we got something
        if len(aliases) > 0:
            # check if array isn't empty
            if aliases[0][0] != "[]" and aliases[0][0] is not None:
                # if not load the array
                aliases_dec = json.loads(aliases[0][0])
            # if array is empty
            else:
                # create
                embed = discord.Embed(
                    title="No aliases added!", color=discord.Color.green()
                )
                # and send embed
                await ctx.send(embed=embed)
                return
        # if there is nothing
        else:
            # create
            embed = discord.Embed(
                title="No aliases added!", color=discord.Color.green()
            )
            # and send embed
            await ctx.send(embed=embed)
            return
        # create base embed
        embed = discord.Embed(title="Added aliases:")
        embed.color = randomColor()
        number = 1
        # for each server id
        for server_index in range(0, len(aliases_dec), 2):
            # get server record from DB
            server_record = await makeAsyncRequest(
                "SELECT ServerObj FROM servers WHERE Id = %s",
                (aliases_dec[server_index],),
            )
            # and decode it
            server_obj = c.ARKServer.fromJSON(server_record[0][0])
            # get alias
            alias = aliases_dec[server_index + 1]
            # add field in embed
            embed.add_field(name=f"{number}. Alias for {server_obj.name}:", value=alias)
        await ctx.send(embed=embed)

    # @commands.bot_has_permissions(
    #     add_reactions=True,
    #     read_messages=True,
    #     send_messages=True,
    #     manage_messages=True,
    #     external_emojis=True,
    # ) 
    @commands.hybrid_command(description="This command will try to fix IP address of a server")
    @app_commands.describe(ip='ip:port to fix')
    async def ipfix(self, ctx, ip: typing.Optional[str]):
        await ctx.defer()  # it will be long
        start = time.perf_counter()  # start timer
        if ip is None:  # if no additional args
            embed = discord.Embed(title="No IP!")
            await ctx.send(embed=embed)
            return
        if IpCheck(ip, checkPort=False) != True:  # IP check
            embed = discord.Embed(title="Something is wrong with **IP**!")
            await ctx.send(embed=embed)
            return
        splitted = ip.split(":")  # split the ip to port and IP
        HEADERS = {"User-Agent": "Magic Browser"}

        # get data from steam API
        async with aiohttp.request(
            "GET",
            f"http://api.steampowered.com/ISteamApps/GetServersAtAddress/v0001?addr={splitted[0]}",
            headers=HEADERS,
        ) as resp:
            text = await resp.json()  # get
            # start of message we will send
            message = """
List of detected servers on that ip by steam:

"""
            # idea 1 : search in DB for those servers ?
            # idea 2 : steam master server queries ? (nope there is no such data there)
            # idea 3 : query only name not whole class worth of data
            # also I can integrate this in server adding process if we know game port (but it still won't help if we don't know any port of the server so I won't depricate this command)
            # if request is successful and we have more that 0 servers
            if (
                bool(text["response"]["success"])
                and text["response"]["servers"].__len__() > 0
            ):
                i = 1
                # for each server in response
                for server in text["response"]["servers"]:
                    ip = server["addr"]  # get ip
                    # try to search for it in DB
                    search = await makeAsyncRequest(
                        "SELECT ServerObj,LastOnline FROM servers WHERE Ip=%s", (ip,)
                    )
                    if search.__len__() <= 0:  # if server isn't in DB
                        # extract ip from 'ip:port' pair
                        addr = ip.split(":")[0]
                        # extract port from 'ip:port' pair
                        port = ip.split(":")[1]
                        try:
                            # get only name of the server (not whole class worth of data)
                            response = await a2s.ainfo((addr, port))
                            # strip version from server's name
                            name = await stripVersion(
                                0, discord.utils.escape_mentions(response.server_name)
                            )
                            # append to the message
                            message += f"{i}. {discord.utils.escape_mentions(ip)} - {name} (Online) \n"
                        except:  # if smt goes wrong
                            # the server is offline
                            message += f"{i}. {discord.utils.escape_mentions(ip)} - ??? (Offline) \n"
                        i += 1  # increase counter
                    else:  # if server is found in DB
                        serverObj = c.ARKServer.fromJSON(
                            search[0][0]
                        )  # construct our class from DB
                        if bool(search[0][1]):  # if server was online
                            # append to the message
                            message += f"{i}. {discord.utils.escape_mentions(ip)} - {serverObj.name} (Online) \n"
                        else:
                            # append to the message
                            message += f"{i}. {discord.utils.escape_mentions(ip)} - {serverObj.name} (Offline) \n"
            else:  # we have no games detected by steam
                # send error message
                await ctx.send("No games found on that IP by steam.")
                return
            message += (
                "Use those ip to add server to bot!"  # append last line to the message
            )

            if message.__len__() >= 2000:  # junk code to send smth over 2k
                await ctx.send(message[:1999])
                # would be replaced with functions from helpers.py
                await ctx.send(message[2000:2999])
            else:
                await ctx.send(message)
            end = time.perf_counter()  # end timer
            # debug
            await sendToMe(
                f"/ipfix exec time: {end - start:.4} sec.\n There was {i-1} servers to fetch",
                self.bot,
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ServerCmd(bot))
