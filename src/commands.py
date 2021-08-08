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


class BulkCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cfg = config.Config()
        self.t = c.Translation()

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
            text=f'Requested by {ctx.author.name} • Bot {self.cfg.version} • GPLv3 ', icon_url=ctx.author.avatar_url)
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
