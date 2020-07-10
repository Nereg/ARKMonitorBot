from helpers import * # all our helpers
import classes as c # all our classes
import discord # main discord lib
from discord.ext import commands
import menus as m
import server_cmd as server # import /server command module (see server_cmd.py)
import json
import config

class NotificationComands(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.cfg = config.Config()
        self.t = c.Translation()

    @commands.command()
    async def watch(self,ctx):
        selector = m.Selector(ctx,self.bot,self.t)
        server = await selector.select()
        if server == '':
            return
        ip = server.ip
        serverId = makeRequest('SELECT Id FROM servers WHERE Ip=%s',(ip,))[0][0]
        notifications = makeRequest('SELECT * FROM notifications WHERE DiscordChannelId=%s AND Type=1',(ctx.channel.id,))
        if (notifications.__len__() <= 0):
            ids = []
            ids.append(serverId)
            makeRequest('INSERT INTO `notifications`(`DiscordChannelId`, `ServersIds`, `Data`, `Sent`, `Type`) VALUES (%s,%s,"{}",0,1)',(ctx.channel.id,json.dumps(ids),))
            await ctx.send(self.t.l['done'])
            return
        else:
            ids = json.loads(notifications[0][4])
            if serverId in ids:
                await ctx.send('You already receive notifications about this server!')
                return
            else:
                ids.append(serverId)
                makeRequest('UPDATE notifications SET ServersIds=%s WHERE DiscordChannelId=%s AND Type=1',(json.dumps(ids),ctx.channel.id,))
                await ctx.send(self.t.l['done'])
                return
            