from helpers import * # all our helpers
import classes as c # all our classes
import discord # main discord lib
from discord.ext import commands
import menus as m
import server_cmd as server # import /server command module (see server_cmd.py)
import json
import config
import datetime
import psutil
from psutil._common import bytes2human
import statistics 

class BulkCommands(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.cfg = config.Config()
        self.t = c.Translation()
    
    @commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True)
    @commands.command()
    async def list(self, ctx):
        servers = '' # string with list of servers
        l = c.Translation()
        if ctx.guild == None : 
            GuildId = ctx.channel.id
            Type = 1
        else:
            GuildId = ctx.guild.id
            Type = 0
        data = makeRequest('SELECT * FROM settings WHERE GuildId=%s AND Type=%s',(GuildId,Type))
        notifications = makeRequest('SELECT * FROM notifications WHERE Type=3')
        channels = ctx.guild.channels
        watchedServers = []
        for notification in notifications:
            if (notification[1] in  [channel.id for channel in ctx.guild.text_channels]):
                watchedServers.append(json.loads(notification[4]))
        if (data.__len__() == 0):
            await ctx.send(l.l['no_servers_added'].format(ctx.prefix))
            return 
        if (data[0][3] == None or data[0][3] == 'null' or data[0][3] == '[]'):
            await ctx.send(l.l['no_servers_added'].format(ctx.prefix))
            return
        else:
            Servers = json.loads(data[0][3]) #remove()
        statement = "SELECT * FROM servers WHERE Id IN ({})".format(', '.join(['{}'.format(Servers[i]) for i in range(len(Servers))]))
        data = makeRequest(statement)
        i = 1 # i (yeah classic)
        for result in data: # fro each record in DB
            #print(result)
            #print(result[0] in watchedServers[0])
            #print(watchedServers)
            server = c.ARKServer.fromJSON(result[4]) # construct our class
            online = bool(result[6]) # exstarct last online state 
            emoji = ':green_circle:' if online else ':red_circle:' # if last online is tru green circle else (if offline) red
            if watchedServers.__len__() > 0:
                watched = '(watched)' if result[0] in watchedServers[0] else ''
            else:
                watched = ''
            name = server.name.find(f'- ({server.version})')
            name = server.name[:name].strip()
            servers += f'{i}. {name} {watched} {emoji} {server.ip}\n' # construct line and add it to all strings
            i += 1 
        # send message
        await ctx.send(f''' 
List of added servers :
{servers}
        ''')
    
    @commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True)
    @commands.command()
    async def info(self, ctx):
        time = datetime.datetime(2000,1,1,0,0,0,0)
        RAM = f'{bytes2human(psutil.virtual_memory().used)}/{bytes2human(psutil.virtual_memory().total)}'
        meUser = self.bot.get_user(277490576159408128)
        role = f'@{ctx.me.roles[1].name}' if 1 in ctx.me.roles else 'No role'
        embed = discord.Embed(title=f'Info about {self.bot.user.name}',timestamp=time.utcnow())
        embed.set_footer(text=f'Requested by {ctx.author.name} • Bot {self.cfg.version} • GPLv3 ',icon_url=ctx.author.avatar_url)
        embed.add_field(name='<:Link:739476980004814898> Invite link',value='[Here!](https://bit.ly/ARKTop)',inline=True)
        embed.add_field(name='<:Github:739476979631521886> GitHub',value='[Here!](https://github.com/Nereg/ARKMonitorBot)',inline=True)
        embed.add_field(name='<:Discord:739476979782254633> Support server',value='[Here!](https://bit.ly/ARKDiscord)',inline=True)
        embed.add_field(name='<:DB:739476980075986976> Servers in database',value=f'{makeRequest("SELECT COUNT(Id) FROM servers")[0][0]}',inline=True)
        embed.add_field(name='<:RAM:739476925852155914> RAM',value=RAM,inline=True)
        embed.add_field(name='<:Bot:748958111456296961> Version',value=self.cfg.version,inline=True)
        embed.add_field(name=':ping_pong: Ping',value=f'{int(self.bot.latency * 1000)} ms',inline=True)
        embed.add_field(name='<:me:739473644874367007> Creator',value=f'{meUser.name}#{meUser.discriminator}',inline=True)
        embed.add_field(name='<:Discord:739476979782254633> Currently in',value=f'{len(self.bot.guilds)} servers',inline=True)
        embed.add_field(name='<:Role:739476980076118046> Role on this server',value=role,inline=True)
        embed.add_field(name=':grey_exclamation: Current prefix',value=f'{get_prefix(1,ctx.message)}',inline=True)
        embed.add_field(name='<:Cpu:739492057990693005> Current CPU utilisation',value=f'{round(statistics.mean(psutil.getloadavg()),1)}',inline=True)
        message = makeRequest('SELECT * FROM settings WHERE GuildId=1')
        if (message.__len__() <= 0):
            message = 'No current message'
        else: 
            message = message[0][4]
        embed.add_field(name='Message from creator',value=message)
        await ctx.send(embed=embed)

    @commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True)
    @commands.command()
    async def ping(self,ctx):
        time = int(self.bot.latency * 1000)
        await ctx.send(self.t.l['ping'].format(time))

    
    @commands.command()
    @commands.is_owner()
    async def count(self,ctx):
        await ctx.send(f'Total guilds count:`{len(self.bot.guilds)}`\nTotal members in that guilds:`{len(self.bot.users)}`')

    @commands.command()
    @commands.is_owner()
    async def stop(self,ctx):
        await ctx.send('Bye!')
        exit()




            