from helpers import * # all our helpers
import classes as c # all our classes
import discord # main discord lib
from discord.ext import commands
import menus as m
import server_cmd as server # import /server command module (see server_cmd.py)
import json
import config
import datetime

class Automessage(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.cfg = config.Config()
        self.t = c.Translation()
    
    async def makeMessage(self,serverId,guildId,serverIp=''):
        if (serverIp != ''):
            server = await makeAsyncRequest('SELECT * FROM Servers WHERE Ip=%s',(serverIp,))
        else:
            server = await makeAsyncRequest('SELECT * FROM Servers WHERE Id=%s',(serverId,))
        serverObj = c.ARKServer.fromJSON(server[0][4])
        playersObj = c.PlayersList.fromJSON(server[0][5])
        alias = await getAlias(serverId,guildId)
        if (alias != ''):
            name = alias
        else:
            name = serverObj.name
        embed=discord.Embed(title=name)
        nameValue = ''
        timevalue = ''
        for player in playersObj.list:
            nameValue += f'{player.name}\n'
            timevalue += f'{player.time}\n'
        embed.add_field(name='Name',value=nameValue,inline=True)
        embed.add_field(name='Time',value=timevalue,inline=True)
        status = ':green_circle: Online' if server[6] == 1 else ':red_circle: Offline'
        embed.add_field(name='Status',value=status,inline=False)
        embed.add_field(name='Ping',value=f'{serverObj.ping} ms',inline=False)
        embed.add_field(name='Map',value=serverObj.map,inline=False)
        embed.add_field(name='IP',value=f'[{serverObj.ip}](steam://connect/{serverObj.ip})')
        return

    async def checkPermissions(self,channel,channel_id=0):
        if (channel_id != 0):
            channel = self.bot.get_channel(channel_id)
            if (channel == None):
                return False
            

    @commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True)
    @commands.command() # CREATE TABLE `bot`.`Automessages` ( `Id` INT NOT NULL AUTO_INCREMENT , `DiscordChannelId` BIGINT NOT NULL , `DiscordMsgId` BIGINT NOT NULL , `ServerId` INT NOT NULL , `Comment` TEXT NULL DEFAULT NULL , PRIMARY KEY (`Id`)) ENGINE = InnoDB; 
    async def automessage(self, ctx, *agrs):        
        channel_converter = discord.ext.commands.TextChannelConverter()
        try:
            channel = await channel_converter.convert(ctx,agrs[0])
        except discord.ext.commands.BadArgument:
            await ctx.send('Channel is not found!')
            return
        selector = m.Selector(ctx,self.bot,c.Translation())
        serverIp = await selector.select()
        if serverIp == '':
            return
        try:
            await channel.send(embed=await self.makeMessage(0,channel.guild.id,serverIp))
        except discord.Forbidden:
            await ctx.send('Cannot send message to selected channel!')
            return

        
    