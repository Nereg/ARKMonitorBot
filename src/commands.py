from helpers import * # all our helpers
import classes as c # all our classes
import discord # main discord lib
from discord.ext import commands
import menus as m
import server_cmd as server # import /server command module (see server_cmd.py)
import json
import config

class BulkCommands(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.cfg = config.Config()
        self.t = c.Translation()
    

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
        if (data.__len__() == 0):
            await ctx.send(l.l['no_servers_added'].format(ctx.prefix))
            return 
        if (data[0][3] == None or data[0][3] == 'null'):
            await ctx.send(l.l['no_servers_added'].format(ctx.prefix))
            return
        else:
            Servers = json.loads(data[0][3]) #remove()
        statement = "SELECT * FROM servers WHERE Id IN ({})".format(', '.join(['{}'.format(Servers[i]) for i in range(len(Servers))]))
        data = makeRequest(statement)
        i = 1 # i (yeah classic)
        for result in data: # fro each record in DB
            server = c.ARKServer.fromJSON(result[4]) # construct our class
            online = bool(result[6]) # exstarct last online state 
            emoji = ':green_circle:' if online else ':red_circle:' # if last online is tru green circle else (if offline) red
            servers += f'{i}. {server.name}  {emoji}  ||{server.ip}|| \n' # construct line and add it to all strings
            i += 1 
        # send message
        await ctx.send(f''' 
Список добавленных серверов :
{servers}
        ''')
    
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
    async def exec(ctx,sql):
        data = makeRequest(sql)
        await ctx.send(data)

    @commands.command()
    @commands.is_owner()
    async def stop(ctx):
        await ctx.send('Bye!')
        exit()




            