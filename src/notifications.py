from helpers import * # all our helpers
import classes as c # all our classes
import discord # main discord lib
from discord.ext import commands
import menus as m
import server_cmd as server # import /server command module (see server_cmd.py)
import json
import config
from server_cmd import ServerCmd
class NotificationComands(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.cfg = config.Config()
        self.t = c.Translation()

    @commands.command()
    async def watch(self,ctx):
        selector = m.Selector(ctx,self.bot,self.t)
        typeSelector = m.NotitifcationSelector(ctx,self.bot,self.t)
        server = await selector.select()        
        if server == '':
            return
        Type = await typeSelector.select()
        if Type == 0: 
            return
        ip = server.ip
        serverId = makeRequest('SELECT Id FROM servers WHERE Ip=%s',(ip,))[0][0]
        notifications2 = makeRequest('SELECT * FROM notifications WHERE DiscordChannelId=%s',(ctx.channel.id,))
        notifications = makeRequest('SELECT * FROM notifications WHERE DiscordChannelId=%s AND Type=%s',(ctx.channel.id,Type,))
        if (notifications.__len__() <= 0):
            ids = []
            ids.append(serverId)
            makeRequest('INSERT INTO `notifications`(`DiscordChannelId`, `ServersIds`, `Data`, `Sent`, `Type`) VALUES (%s,%s,"{}",0,%s)',(ctx.channel.id,json.dumps(ids),Type,))
            await ctx.send(self.t.l['done'])
            return
        else:
            ids = json.loads(notifications[0][4])
            if serverId in ids:
                await ctx.send('You already receive notifications about this server!')
                return
            else:
                ids.append(serverId)
                makeRequest('UPDATE notifications SET ServersIds=%s WHERE DiscordChannelId=%s AND Type=%s',(json.dumps(ids),ctx.channel.id,Type,))
                await ctx.send(self.t.l['done'])
                return

    @commands.command()
    async def autolist(self,ctx):
        selector = m.Selector(ctx,self.bot,c.Translation())
        server = await selector.select()
        if server == '':
            return
        embedMaker = ServerCmd(self.bot)
        playersList = makeRequest('SELECT * FROM servers WHERE Ip=%s',(server.ip,))
        embed = embedMaker.serverInfo(server,c.PlayersList.fromJSON(playersList[0][5]),True)
        print(embed)
        msg = await ctx.send(embed)
        await ctx.send('Bot will update last message!')
        makeRequest('INSERT INTO notifications (`DiscordChannelId`, `Type`, `Sent`, `ServersIds`, `Data`) VALUES (%s,124,0,%s,%s)',(ctx.channel.id,str(playersList[0][0]),str(msg.id),))

    @commands.command()
    async def eos(self,ctx):
        server = makeRequest('SELECT * FROM settings WHERE GuildId=%s',(ctx.guild.id,))
        channelId = ctx.channel.id
        notifications = makeRequest('SELECT * FROM notifications WHERE Type=123')
        for record in notifications:
            if (record[1] == channelId):
                await ctx.send('OK you won`t recive any notifications now!')
                makeRequest('DELETE FROM notifications WHERE DiscordChannelId=%s',(channelId,))
                return
        await ctx.send('OK! Bot will send message here if someone will join or leave any added servers!')
        makeRequest('INSERT INTO notifications (`DiscordChannelId`, `Type`, `Sent`, `ServersIds`, `Data`) VALUES (%s,123,0,"[]",%s)',(ctx.channel.id,str(server[0][1]),))
            