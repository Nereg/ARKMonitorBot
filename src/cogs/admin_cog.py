from cogs.utils.helpers import *
from cogs.utils.location import Location
import cogs.utils.classes as c
from cogs.utils.menus import *
import discord  # main discord library
from discord.ext import commands  # import commands extension
import json
import aiohttp
import cogs.utils.classes as c


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.cfg = config.Config()
        self.bot = bot

    async def cog_check(self, ctx):
        return (
            await self.bot.is_owner(ctx.author)
            or ctx.author.id == 277490576159408128
            and not is_slash(ctx)
        )

    @commands.command(slash_command=False, hidden=True)
    async def exec(self, ctx, sql):
        data = await makeAsyncRequest(sql)
        await ctx.send(data)

    @commands.command(slash_command=False, hidden=True)
    async def test(self, ctx):
        text = '{"py/object": "c.ARKServer", "ip": "192.223.27.63:27001", "address": "192.223.27.63", "port": 27001, "name": "Bacon Blitz 8/27 100x/Shop/Kit/S+/flyerspeed/4man - (v678.10)", "version": "v678.10", "stripedName": "Bacon Blitz 8/27 100x/Shop/Kit/S+/flyerspeed/4man", "serverSteamId": 90150868627673092, "platform": "Windows", "online": 68, "maxPlayers": 100, "map": "Ragnarok", "password": false, "PVE": false, "clusterName": "Cluster0001", "mods": ["849985437", "1999447172", "1231538641", "2183584447"], "isARK": true, "game_id": 346110, "ping": 141}'
        testClass = c.ARKServer.fromJSON(text)
        await ctx.send(testClass)
        await ctx.send(type(testClass))

    @commands.command(slash_command=False, hidden=True)
    async def error(self, ctx):
        await ctx.send("A" * 5000)

    @commands.command(slash_command=False, hidden=True)
    async def getIpLocation(self, ctx, ip: str):
        session = aiohttp.ClientSession()
        loc = Location(session)
        code = await loc.get(ip)
        emoji = await loc.getEmoji(code)
        await ctx.send(f"Ip: `{ip}`\nCountry code: `{code}`\nCountry emoji: {emoji}")

    @commands.command(slash_command=False, hidden=True)
    async def setMessage(self, ctx, message):
        result = await makeAsyncRequest("SELECT * FROM settings WHERE GuildId=1")
        if result.__len__() <= 0:
            await makeAsyncRequest(
                'INSERT INTO settings(GuildId, Prefix, ServersId, Admins, Type, Aliases) VALUES (1,"","","",0,"")'
            )
        await makeAsyncRequest(
            "UPDATE settings SET Admins=%s WHERE GuildId=1", (message,)
        )
        await ctx.send("Done!")

    @commands.command(slash_command=False, hidden=True)
    async def deleteMessage(self, ctx, channelId: int, messageId: int):
        channel = self.bot.get_channel(channelId)
        if channel == None:
            await ctx.send("Wrong channel id")
        else:
            try:
                message = await channel.fetch_message(messageId)
            except BaseException as e:
                await ctx.send("error")
                await ctx.send(e)
                return
            await message.delete()
            await ctx.send("Done !")

    @commands.command(slash_command=False, hidden=True)
    async def restart(self, ctx):
        await ctx.send("Good bye my friend!")
        exit(12121312)
        return
    
    @commands.command(slash_command=False, hidden=True)
    async def deleteServer(self, ctx, serverIp: str):
        await deleteServer(serverIp)
    
    async def purge(self, ctx, value: int):
        servers = await makeAsyncRequest(
            "SELECT Id FROM servers WHERE OfflineTrys >= %s", (value,)
        )
        for server in servers:
            id = server[0]
            result = await deleteServer("", id)
            if result != 0:
                await ctx.send(f"Smt went wrong with server {id}!")
        await ctx.send("Deleted servers!")
        return

    @commands.command(slash_command=False, hidden=True)
    async def purgeServers(self, ctx, *argv):
        if argv.__len__() <= 0:
            await ctx.send("Not every parameter was supplied!")
            return
        elif str.isdigit(argv[0]):
            value = int(argv[0])
        else:
            await ctx.send(f"`{ argv[0]}` isn't a number!")
            return
        machedServers = await makeAsyncRequest(
            "SELECT COUNT(*) FROM `servers` WHERE OfflineTrys >= %s", (value,)
        )
        self.msg = await ctx.send(
            f"Do you really want to delete {machedServers[0][0]} servers?"
        )
        await self.msg.add_reaction("✅")
        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add",
                timeout=100,
                check=lambda r, user: user != self.bot.user
                and r.message.id == self.msg.id,
            )
        except asyncio.TimeoutError:
            try:
                await self.msg.clear_reactions()
                await self.msg.edit(
                    content="The interactive menu was closed.", embed=None
                )
            # It was SO ANNOYING ! DONT DELET MESSAGES THERE ARE STOP BUTTON! (yeah I pasted this code from user space why not)
            except discord.errors.NotFound:
                return ""
        else:
            if str(reaction.emoji) == "✅":
                await ctx.send("Ok! Deleting!")
                await self.msg.clear_reactions()
                await self.purge(ctx, value)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AdminCog(bot))
