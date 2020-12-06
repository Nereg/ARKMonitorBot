from helpers import * # all our helpers
import classes as c # all our classes
import discord # main discord lib
from discord.ext import commands ,tasks
import menus as m
import server_cmd as server # import /server command module (see server_cmd.py)
import json
import config
import datetime
import time

class Automessage(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.cfg = config.Config()
        self.t = c.Translation()
        self.updater.start()
    
    async def deleteAutomessage(self,recordId):
        #raise BaseException('DELETE')
        record = await makeAsyncRequest('SELECT * FROM automessages WHERE Id=%s',(recordId,))
        await sendToMe(f'Deleted automessage {record[0][2]} in server guild {record[0][5]}')
        #await makeAsyncRequest('DELETE FROM automessages WHERE Id=%s',(recordId,))

    async def makeMessage(self,serverId,guildId,serverIp=''):
        if (serverIp != ''):
            server = await makeAsyncRequest('SELECT * FROM servers WHERE Ip=%s',(serverIp,))
        else:
            server = await makeAsyncRequest('SELECT * FROM servers WHERE Id=%s',(serverId,))
        serverObj = c.ARKServer.fromJSON(server[0][4])
        playersObj = c.PlayersList.fromJSON(server[0][5])
        alias = await getAlias(serverId,guildId)
        if (alias != ''):
            name = alias
        else:
            name = await stripVersion(serverObj)
        embed=discord.Embed(title=name)
        if (playersObj.list.__len__() > 0):
            nameValue = ''
            timevalue = ''
            for player in playersObj.list:
                nameValue += f'{player.name}\n'
                timevalue += f'{player.time}\n'        
            embed.add_field(name='Name',value=nameValue,inline=True)
            embed.add_field(name='Time',value=timevalue,inline=True)
        else:
            embed.add_field(name='No one is on the server',value='\u200B',inline=True)
        status = ':green_circle: Online' if server[0][6] == 1 else ':red_circle: Offline'
        embed.add_field(name='Status',value=status,inline=False)
        embed.add_field(name='Ping',value=f'{serverObj.ping} ms',inline=True)
        embed.add_field(name='Map',value=serverObj.map,inline=True)
        embed.add_field(name='IP',value=f'{serverObj.ip}',inline=True)
        curTime = datetime.datetime.utcnow()
        embed.set_footer(text=f'Updated: {curTime.strftime("%m.%d at %H:%M")} (UTC)')
        return embed

    async def checkPermissions(self,channel,channel_id=0): #check for : send,edit messages , use external emojis, ...
        if (channel_id != 0):
            channel = self.bot.get_channel(channel_id)
            if (channel == None):
                return False
        permissions = channel.permissions_for(channel.guild.me)
        p = permissions
        if (p.read_messages and p.send_messages and p.manage_messages and p.embed_links and p.external_emojis):
            return True



    @tasks.loop(seconds=60)
    async def updater(self):
        automessages = await makeAsyncRequest('SELECT * FROM automessages')
        for message in automessages:
            channel = self.bot.get_channel(message[1])
            if (channel == None):
                await self.deleteAutomessage(message[0])
                continue
            if (not await self.checkPermissions(channel)):
                await self.deleteAutomessage(message[0])
                continue
            try:
                discordMessage = await channel.fetch_message(message[2])
            except discord.NotFound:
                await self.deleteAutomessage(message[0])
                continue
            embed = await self.makeMessage(message[3],channel.guild.id)
            await discordMessage.edit(embed=embed)
        return    

    @updater.before_loop
    async def before_printer(self):
        #print('waiting...')
        await self.bot.wait_until_ready()

    @commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True)
    @commands.command() # CREATE TABLE `bot`.`automessages` ( `Id` INT NOT NULL AUTO_INCREMENT , `DiscordChannelId` BIGINT NOT NULL , `DiscordMsgId` BIGINT NOT NULL , `ServerId` INT NOT NULL , `Comment` TEXT NULL DEFAULT NULL , PRIMARY KEY (`Id`)) ENGINE = InnoDB; 
    async def automessage(self, ctx, *agrs):        
        channel_converter = discord.ext.commands.TextChannelConverter()
        try:
            channel = await channel_converter.convert(ctx,agrs[0])
        except discord.ext.commands.BadArgument:
            if (agrs[0] != 'delete'):
                await ctx.send('You submitted invalid channel!')
                return
            else:
                selector = m.Selector(ctx,self.bot,c.Translation())
                serverIp = await selector.select()
                if serverIp == '':
                    return
                server = await makeAsyncRequest('SELECT * FROM servers WHERE Ip=%s',(serverIp.ip,))
                server = server[0]
                messages = await makeAsyncRequest('SELECT * FROM automessages WHERE ServerId=%s AND DiscordGuildId=%s',(server[0],ctx.guild.id,))
                if (messages.__len__() <= 0):
                    embed = discord.Embed(title='You have no automessage for that server!')
                    embed.set_footer(text=f'Requested by {ctx.author.name} • Bot {self.cfg.version} • GPLv3 ',icon_url=ctx.author.avatar_url)
                    await ctx.send(embed=embed)
                    return
                else:
                    embed = discord.Embed(title='Delete that message?')
                    serverObj = c.ARKServer.fromJSON(server[4])
                    alias = await getAlias(server[0],ctx.guild.id)
                    name = await stripVersion(serverObj) if alias == '' else alias
                    link = f'https://discordapp.com/channels/{ctx.guild.id}/{messages[0][1]}/{messages[0][2]}'
                    channelMention = self.bot.get_channel(messages[0][1])
                    if (channelMention == None):
                        channelMention = '#deleted-channel'
                    else:
                        channelMention = channelMention.mention
                    embed.add_field(name=f'For server {name}',value=f'[Message]({link}) in {channelMention}')
                    embed.set_footer(text=f'Requested by {ctx.author.name} • Bot {self.cfg.version} • GPLv3 ',icon_url=ctx.author.avatar_url)
                    msg = await ctx.send(embed=embed)
                    self.msg = msg
                    await msg.add_reaction('✅')
                    await msg.add_reaction('❎')
                    try:
                        reaction,user = await self.bot.wait_for('reaction_add',timeout=100,check=lambda r,user: user != self.bot.user and r.message.id == self.msg.id)
                    except asyncio.TimeoutError:
                        try:
                            await self.msg.clear_reactions()
                            await self.msg.edit(content='The interactive menu was closed.',embed=None)
                        except discord.errors.NotFound: # It was SO ANNOYING ! DONT DELET MESSAGES THERE ARE STOP BUTTON!  
                            return
                    else:
                        if (str(reaction.emoji) == '✅'):
                            await self.msg.clear_reactions()
                            await makeAsyncRequest('DELETE FROM automessages WHERE ServerId=%s',(server[0],))
                            await self.msg.edit(content='Done! You can now safely delete that message!',embed=None)
                            return
                        if (str(reaction.emoji) == '❎'):
                            await self.msg.clear_reactions()
                            await self.msg.delete()
                            return
                return
        except IndexError:
            messages = await makeAsyncRequest('SELECT * FROM automessages WHERE DiscordGuildId=%s',(ctx.guild.id,))   
            embed = discord.Embed(title='List of auto messages:')
            i = 1
            for message in messages:
                alias = await getAlias(message[3],ctx.guild.id)
                server = await makeAsyncRequest('SELECT ServerObj FROM servers WHERE Id=%s',(message[3],))
                serverObj = c.ARKServer.fromJSON(server[0][0])
                name = await stripVersion(serverObj) if alias == '' else alias
                link = f'https://discordapp.com/channels/{ctx.guild.id}/{message[1]}/{message[2]}'
                channelMention = self.bot.get_channel(message[1])
                if (channelMention == None):
                    channelMention = '#deleted-channel'
                else:
                    channelMention = channelMention.mention
                embed.add_field(name=f'{i}) Message for {name}:', value=f'[Message]({link}) in {channelMention}')
                i += 1
            if (messages.__len__() <= 0):
                embed.add_field(name='Oops seems like you have no auto messages!',value=f'But you can add them via {ctx.prefix}automessage #channel_you_want')
            embed.set_footer(text=f'Requested by {ctx.author.name} • Bot {self.cfg.version} • GPLv3 ',icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
            return
        if (not await self.checkPermissions(channel)):
            await ctx.send('Cannot send mesage to that channel! Please check if bot has those permisions in selected channel: \n```Send & manage & read messages\nEmbed links\nUse external emojis```')
            return
        selector = m.Selector(ctx,self.bot,c.Translation())
        serverIp = await selector.select()
        if serverIp == '':
            return       
        server = await makeAsyncRequest('SELECT Id FROM servers WHERE Ip=%s',(serverIp.ip,))
        automessages = await makeAsyncRequest('SELECT * FROM automessages WHERE ServerId = %s',(server[0][0]))
        if (automessages.__len__() >= 1):
            link = f'https://discordapp.com/channels/{ctx.guild.id}/{automessages[0][1]}/{automessages[0][2]}'
            await ctx.send(f'You already have message(<{link}>) for that server!')
            return
        try:
            message = await channel.send(embed=await self.makeMessage(0,channel.guild.id,serverIp.ip))
        except discord.Forbidden:
            await ctx.send('Cannot send message to selected channel!')
            return
        await makeAsyncRequest('INSERT INTO automessages (`DiscordChannelId`, `DiscordMsgId`, `ServerId`, `DiscordGuildId`) VALUES (%s,%s,%s,%s)',(channel.id,message.id,server[0][0],ctx.guild.id,))
        await ctx.send('All done! I will update that message!')

        
    