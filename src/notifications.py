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

    @commands.command
    async def watch(self,ctx):
        selector = m.Selector(ctx,self.bot,self.t)
        server = await selector.select()
        if server == '':
            return
        ip = server.ip
        serverId = makeRequest('SELECT * FROM servers WHERE Ip=%s',(ip,))
        serverId = int(serverId[0][0])
        notificationsRecord = makeRequest('SELECT * FROM notifications WHERE ChannelId=%s AND Type=1',(ctx.channel.id))
        if notificationsRecord.__len__() <= 0:
            serverIds = [serverId]
            serverIds = json.dumps(serverIds)
            makeRequest('INSERT INTO `notifications`(`ChannelId`, `ServerIds`, `Data`, `Language`, `Delivered`, `Type`) VALUES (%s,%s,"{}",%s,0,1)',(ctx.channel.id,serverIds,self.t.lang))
            await ctx.send(self.t.l['done'])
        else:
            notificationsRecord = json.loads(notificationsRecord[0][2])
            if serverId in notificationsRecord:
                await ctx.send('You already receive notifications about that server!')
                return
            notificationsRecord.append(serverId)
            await ctx.send(self.t.l['done'])
            makeRequest('UPDATE notifications SET ServerIds=%s WHERE ChannelId=%s AND Type=1',(json.dumps(notificationsRecord),ctx.channel.id))
    
