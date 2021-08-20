from helpers import *  # all our helpers
import classes as c  # all our classes
import discord  # main discord lib
from discord.ext import commands
import menus as m
# import /server command module (see server_cmd.py)
import server_cmd as server
import json
import config
import datetime
import psutil
from psutil._common import bytes2human
import statistics
import time
import arrow

class BulkCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cfg = config.Config()
        self.t = c.Translation()

    async def listServers(self, ctx):
        # select settings of the guild
        settings = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=%s', (ctx.guild.id,))
        # get ids of added servers in this guild
        serversIds = json.loads(settings[0][3])
        # if we have no servers added
        if (serversIds.__len__() <= 0):
            # create error embed
            embed = discord.Embed()
            # add title
            embed.title = 'Looks like you have no servers added!'
            # and description
            embed.description = f'You can add any steam server using `{ctx.prefix}server add` command!'
            # and return
            return embed
        # empty statement
        statement = "SELECT * FROM servers WHERE Id IN ({})"
        # SELECT * FROM servers WHERE Id IN (1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 150)
        # make IN (...) part
        #await ctx.send(serversIds)
        # problem here
        param = ', '.join([str(i) for i in serversIds]) 
        #await ctx.send(param)
        # make request
        #await ctx.send(statement.format(param))
        servers = await makeAsyncRequest(statement.format(param))
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
        pass

    async def listAutoMessages(self, ctx):
        pass

    @commands.bot_has_permissions(add_reactions=True, read_messages=True, send_messages=True, manage_messages=True, external_emojis=True)
    @commands.command()
    async def neolist(self, ctx):
        # TODO re-do this to use multiple embeds in one message (need d.py 2.0 for that)
        await ctx.send(embed = await self.listServers(ctx))
        pass

    @commands.bot_has_permissions(add_reactions=True, read_messages=True, send_messages=True, manage_messages=True, external_emojis=True)
    @commands.command()
    async def list(self, ctx):
        servers = ''  # string with list of servers
        l = c.Translation()  # load translation
        GuildId = ctx.guild.id
        Type = 0  # lefovers of old code (supposed support for DM's)
        # get settings of current guild
        data = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=%s AND Type=%s', (GuildId, Type))
        # select server notifications
        notifications = await makeAsyncRequest('SELECT * FROM notifications WHERE Type=3')
        watchedServers = []  # list of watched servers
        # most bugged and required part of the bot AFAIK (no updater is lol)
        for notification in notifications:  # for notifications
            # if bot will notify in current channel (not in some channel of the guild and it is a new feature to make)
            if (notification[1] == ctx.channel.id):
                # append server id in list
                watchedServers.append(json.loads(notification[4]))
        if (data.__len__() == 0):  # if
            await ctx.send(l.l['no_servers_added'].format(ctx.prefix))
            return
        if (data[0][3] == None or data[0][3] == 'null' or data[0][3] == '[]'):
            await ctx.send(l.l['no_servers_added'].format(ctx.prefix))
            return
        else:
            Servers = json.loads(data[0][3])  # remove()
        statement = "SELECT * FROM servers WHERE Id IN ({})".format(
            ', '.join(['{}'.format(Servers[i]) for i in range(len(Servers))]))
        await ctx.send(statement)
        data = await makeAsyncRequest(statement)
        i = 1  # i (yeah classic)
        for result in data:  # from each record in DB
            # print(result)
            #print(result[0] in watchedServers[0])
            # print(watchedServers)
            server = c.ARKServer.fromJSON(result[4])  # construct our class
            online = bool(result[6])  # exstarct last online state
            # if last online is tru green circle else (if offline) red
            emoji = ':green_circle:' if online else ':red_circle:'
            if watchedServers.__len__() > 0:
                watched = '(watched)' if result[0] in watchedServers[0] else ''
            else:
                watched = ''
            alias = await getAlias(result[0], ctx.guild.id)
            if(alias == ''):
                name = server.name.find(f'- ({server.version})')
                name = server.name[:name].strip()
            else:
                name = alias
            # construct line and add it to all strings
            servers += f'{i}. {name} ({server.map}) {watched} {emoji} {server.ip}\n'
            i += 1
        # send message
        await ctx.send(f''' 
List of added servers :
{discord.utils.escape_mentions(servers)}
        ''')

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
            text=f'Requested by {ctx.author.name} • Bot {self.cfg.version} • Uptime: {self.getUptime()} ', icon_url=ctx.author.avatar_url)
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
