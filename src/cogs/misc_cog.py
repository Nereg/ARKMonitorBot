from cogs.utils.helpers import *  # all our helpers
import cogs.utils.classes as c  # all our classes
import discord  # main discord lib
from discord.ext import commands
import cogs.utils.menus as m
# import /server command module (see server_cmd.py)
#import server_cmd as server
import json
import config
import datetime
import psutil
from psutil._common import bytes2human
import statistics
import time
import arrow


class MiscCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cfg = config.Config()
        self.t = c.Translation()
        self.slashCommands = ['info']

    async def slashHandler(self, interaction):
        await self.slashInfo(interaction)
        pass

    async def selectServersByIds(self, ids):
        # empty statement
        statement = "SELECT * FROM servers WHERE Id IN ({})"
        # construct part of the query
        param = ', '.join([str(i) for i in ids]) 
        print(statement.format(param))
        # return result
        return await makeAsyncRequest(statement.format(param))


    def noServers(self, ctx):
        # create error embed
        embed = discord.Embed()
        # paint it 
        embed.color = randomColor()
        # add title
        embed.title = 'Looks like you have no servers added!'
        # and description
        embed.description = f'You can add any steam server using `{ctx.prefix}server add` command!'
        # and return
        return embed

    async def listServers(self, ctx):
        # select settings of the guild
        settings = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=%s', (ctx.guild.id,))
        # if no settings found 
        if (settings.__len__() <= 0 or settings[0][3] == None):
            # send no servers embed
            return self.noServers(ctx)
        # get ids of added servers in this guild
        serversIds = json.loads(settings[0][3])
        # if we have no servers added
        if (serversIds.__len__() <= 0):
            # return no servers embed
            return self.noServers(ctx)
        # select servers by ids
        servers = await self.selectServersByIds(serversIds)
        # create embed
        embed = discord.Embed()
        # paint it 
        embed.color = randomColor()
        # set title 
        embed.title = 'List of servers:'
        # index of the first server
        i = 1
        # for each server
        for server in servers:
            # load server object
            serverObj = c.ARKServer.fromJSON(server[4])
            # load more info about server
            info = json.loads(server[8])
            # create field name
            fieldName = f'{i}. {await stripVersion(serverObj)}'
            # if server is online set status to online string
            # else to offline string 
            status = ':green_circle: Online' if server[6] == 1 else ':red_circle: Offline'
            # create field value
            fieldValue = f'[{server[1]}]({info.get("battleUrl","")}) {status}'
            # add field to embed
            embed.add_field(name = fieldName, value = fieldValue)
            # increment index 
            i += 1
        # return embed
        return embed


    async def listNotifications(self, ctx):
        # select all notifications for current guild
        # (won't work with old table format)
        notifications = await makeAsyncRequest('SELECT * FROM notifications WHERE GuildId = %s',(ctx.guild.id,))
        # if there are no notifications
        if (notifications.__len__() <= 0):
            # return nothing
            return None
        # create embed
        embed = discord.Embed()
        # paint it 
        embed.color = randomColor()
        # add title 
        embed.title = 'List of notifications:'
        # notification index
        i = 1
        # for each record in db
        for record in notifications:
            # load server ids
            serverIds = json.loads(record[4])
            # if no servers in record
            if (serverIds.__len__() <= 0):
                # skip it
                continue
            # load server records
            servers = await self.selectServersByIds(serverIds)
            # for each server
            for server in servers:
                # make server object from record
                server = c.ARKServer.fromJSON(server[4])
                # make name and value
                name = f'{i}. Notification for `{await stripVersion(server)}`'
                value = f'In <#{record[1]}>'
                # and add field
                embed.add_field(name = name, value = value)
                i += 1
        # if no fields were added
        if (i <= 1):
            return None
        # else return embed
        return embed


    async def listAutoMessages(self, ctx):
        # select all messages for this guild
        records = await makeAsyncRequest('SELECT * FROM automessages WHERE DiscordGuildId = %s',(ctx.guild.id,))
        # if no records found
        if (records.__len__() <= 0):
            # return nothing
            return None
        # create embed
        embed = discord.Embed()
        # paint it
        embed.color = randomColor()
        # add title 
        embed.title = 'List of auto messages:'
        # get ids of all servers in records
        serversIds = [record[3] for record in records]
        # get servers from those ids
        servers = await self.selectServersByIds(serversIds)
        # auto message index
        index = 1
        # for each record
        for i, record in enumerate(records):
            # create server object from server record
            server = c.ARKServer.fromJSON(servers[i][4])
            # create link to message from auto message record
            msgLink = f'https://discordapp.com/channels/{ctx.guild.id}/{record[1]}/{record[2]}'
            # create name and value for field
            name = f'{index}. Message for `{await stripVersion(server)}`'
            value = f'[Message]({msgLink}) in <#{record[1]}>'
            # add field
            embed.add_field(name = name, value = value)
            index += 1
        # return embed
        return embed


    def getUptime(self):
        # get current process
        proc = psutil.Process()
        # get process creation date
        # (in float UNIX timestamp)
        creationTime = arrow.get(proc.create_time())
        # get current time in UNIX timestamp
        currentTime = arrow.utcnow()
        # get uptime
        uptime = currentTime - creationTime
        # get components of datetime.timedelta
        # where is .format() python ?!
        days = uptime.days
        seconds = uptime.seconds % 60
        hours = uptime.seconds//3600
        minutes = (uptime.seconds//60) % 60
        # if less then 1 hour
        if (hours == 0):
            # return just minutes + seconds
            return f"{minutes}:{seconds}"
        # if less than 1 day
        elif (days == 0):
            # return just hours + minutes + seconds
            return f"{hours}:{minutes}:{seconds}"
        else:
            # return full string
            return f"{days}:{hours}:{minutes}:{seconds}"


    @commands.bot_has_permissions(add_reactions=True, read_messages=True, send_messages=True, manage_messages=True, external_emojis=True)
    @commands.command()
    async def list(self, ctx):
        # TODO re-do this to use multiple embeds in one message (need d.py 2.0 for that)
        # IDEA maybe you can select what you are trying to list ? like :
        # /list servers, /list notifications
        # make all coroutines
        coroutines = [self.listServers(ctx),
                    self.listNotifications(ctx),
                    self.listAutoMessages(ctx)] 
        # run them concurrently
        embeds = await asyncio.gather(*coroutines)
        # for each embed
        for embed in embeds:
            # if we have some embed
            if (embed != None):
                # send it
                await ctx.send(embed = embed)


    @commands.bot_has_permissions(add_reactions=True, read_messages=True, send_messages=True, manage_messages=True, external_emojis=True)
    @commands.command()
    async def info(self, ctx):
        # get how many servers we have in DB
        count = await makeAsyncRequest("SELECT COUNT(Id) FROM servers")
        # get object to get time
        time = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        # get total and used memory in the system
        RAM = f'{bytes2human(psutil.virtual_memory().used)}/{bytes2human(psutil.virtual_memory().total)}'
        # get bot's role
        role = ctx.me.top_role.mention if ctx.me.top_role != "@everyone" else "No role"
        # create embed
        embed = discord.Embed(
            title=f'Info about {self.bot.user.name}', timestamp=time.utcnow(), color=randomColor())
        # set footer
        embed.set_footer(
            text=f'Requested by {ctx.author.name} • Bot {self.cfg.version} • Uptime: {self.getUptime()} ', icon_url=ctx.author.display_avatar)
        # add fields
        embed.add_field(name='<:Link:739476980004814898> Invite link',
                        value='[Here!](https://bit.ly/ARKTop)', inline=True)
        embed.add_field(name='<:Github:739476979631521886> GitHub',
                        value='[Here!](https://github.com/Nereg/ARKMonitorBot)', inline=True)
        embed.add_field(name='<:Discord:739476979782254633> Support server',
                        value='[Here!](https://bit.ly/ARKDiscord)', inline=True)
        embed.add_field(name='<:DB:739476980075986976> Servers in database',
                        value=f'{count[0][0]}', inline=True)
        embed.add_field(name='<:RAM:739476925852155914> RAM',
                        value=RAM, inline=True)
        embed.add_field(name='<:Bot:748958111456296961> Version',
                        value=self.cfg.version, inline=True)
        embed.add_field(name=':ping_pong: Ping',
                        value=f'{int(self.bot.latency * 1000)} ms', inline=True)
        embed.add_field(name='<:me:739473644874367007> Creator',
                        value=f'Nereg#7006', inline=True)
        embed.add_field(name='<:Discord:739476979782254633> Currently in',
                        value=f'{len(self.bot.guilds)} servers', inline=True)
        embed.add_field(
            name='<:Role:739476980076118046> Role on this server', value=role, inline=True)
        embed.add_field(name=':grey_exclamation: Current prefix', value=f'{await get_prefix(1,ctx.message)}', inline=True)
        embed.add_field(name='<:Cpu:739492057990693005> Current CPU utilisation',
                        value=f'{round(statistics.mean(psutil.getloadavg()),1)}', inline=True)
        # guild 1 is special value
        message = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=1')
        if (message.__len__() <= 0):
            message = 'No current message'
        else:
            message = message[0][4]
        embed.add_field(name='Message from creator', value=message)
        await ctx.send(embed=embed)

    async def slashInfo(self, interaction):
        # get how many servers we have in DB
        count = await makeAsyncRequest("SELECT COUNT(Id) FROM servers")
        # get object to get time
        time = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        # get total and used memory in the system
        RAM = f'{bytes2human(psutil.virtual_memory().used)}/{bytes2human(psutil.virtual_memory().total)}'
        # get bot's role
        role = interaction.guild.me.top_role.mention if interaction.guild.me.top_role != "@everyone" else "No role"
        # create embed
        embed = discord.Embed(
            title=f'Info about {self.bot.user.name}', timestamp=time.utcnow(), color=randomColor())
        # set footer
        embed.set_footer(
            text=f'Requested by {interaction.user.name} • Bot {self.cfg.version} • Uptime: {self.getUptime()} ', icon_url=interaction.user.display_avatar)
        # create view
        view = discord.ui.View()
        # add buttons (yay)
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.link,
                                        label='Our support guild',
                                        emoji='<:Discord:739476979782254633>',
                                        url='https://bit.ly/ARKDiscord'
                                        ))
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.link,
                                        label='GitHub',
                                        emoji='<:Github:739476979631521886>',
                                        url='https://github.com/Nereg/ARKMonitorBot'
                                        ))
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.link,
                                        label='Invite link',
                                        emoji='<:Link:739476980004814898>',
                                        url='https://bit.ly/ARKTop'
                                        ))
        # add fields
        embed.add_field(name='<:DB:739476980075986976> Servers in database',
                        value=f'{count[0][0]}', inline=True)
        embed.add_field(name='<:RAM:739476925852155914> RAM',
                        value=RAM, inline=True)
        embed.add_field(name='<:Bot:748958111456296961> Version',
                        value=self.cfg.version, inline=True)
        embed.add_field(name=':ping_pong: Ping',
                        value=f'{int(self.bot.latency * 1000)} ms', inline=True)
        embed.add_field(name='<:me:739473644874367007> Creator',
                        value=f'Nereg#7006', inline=True)
        embed.add_field(name='<:Discord:739476979782254633> Currently in',
                        value=f'{len(self.bot.guilds)} servers', inline=True)
        embed.add_field(
            name='<:Role:739476980076118046> Role on this server', value=role, inline=True)
        embed.add_field(name=':grey_exclamation: Current prefix', value=f'You are using slash commands!', inline=True)
        embed.add_field(name='<:Cpu:739492057990693005> Current CPU utilisation',
                        value=f'{round(statistics.mean(psutil.getloadavg()),1)}', inline=True)
        # guild 1 is special value
        message = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=1')
        if (message.__len__() <= 0):
            message = 'No current message'
        else:
            message = message[0][4]
        embed.add_field(name='Message from creator', value=message)
        await interaction.response.send_message(embed=embed, view=view)
    
def setup(bot: commands.Bot) -> None:
    cog = MiscCommands(bot)
    bot.add_cog(cog)
    bot.myCogs.append(cog)
