from discord.ext import menus
from helpers import * # all our helpers
import classes as c
import asyncio
import json
import datetime

class Selector():
    def __init__(self,ctx,bot,lang):
        self.ctx = ctx
        self.bot = bot
        self.l = lang # classes.Translation 
        pass

    def createEmbed(self, data,number):
        server = c.ARKServer.fromJSON(data[number][4])
        online = bool(data[number][6])
        embed = discord.Embed(title=f'{number+1}. {server.name}')
        status = ':green_circle: '+ self.l.l['online'] if online else ':red_circle: ' + self.l.l['offline']
        pve = self.l.l['yes'] if server.PVE else self.l.l['no']
        embed.add_field(name='IP',value=server.ip)
        embed.add_field(name=self.l.l['status'],value=status)
        embed.add_field(name=self.l.l['version'],value=f'{server.version}')
        embed.add_field(name='PVE?',value=pve)
        embed.add_field(name=self.l.l['players_count'],value=f'{server.online}/{server.maxPlayers}')
        return embed

    async def select(self):
        reactions = ['⏮️','\u2B05','\u2705','\u27A1','⏭️','\u23F9']
        if self.ctx.guild == None : 
            GuildId = self.ctx.channel.id
            Type = 1
        else:
            GuildId = self.ctx.guild.id
            Type = 0
        data = makeRequest('SELECT * FROM settings WHERE GuildId=%s AND Type=%s',(GuildId,Type))
        if (data.__len__() == 0):
            await self.ctx.send(self.l.l['no_servers_added'].format(self.ctx.prefix))
            return ''
        if (data[0][3] == None or data[0][3] == 'null' or data[0][3] == '[null]'):
            await self.ctx.send(self.l.l['no_servers_added'].format(self.ctx.prefix))
            return ''
        else:
            Servers = json.loads(data[0][3])
        statement = "SELECT * FROM servers WHERE Id IN ({})".format(', '.join(['{}'.format(Servers[i]) for i in range(len(Servers))]))
        print(statement)
        data = makeRequest(statement)
        try:
            self.msg = await self.ctx.send(self.l.l['server_select'],embed=self.createEmbed(data,0))
        except IndexError:
            await self.ctx.send(self.l.l['no_servers_added'].format(self.ctx.prefix))
            return ''
        for reaction in reactions:
            await self.msg.add_reaction(reaction)
        flag = 0
        counter = 0
        selected = False
        while flag == 0:
            try:
                reaction,user = await self.bot.wait_for('reaction_add',timeout=100,check=lambda r,user: user != self.bot.user and r.message.id == self.msg.id)
            except asyncio.TimeoutError:
                flag = 1
                await self.msg.clear_reactions()
                await self.msg.edit(content='Selector has timed out.',embed=None)
            else :
                if (str(reaction.emoji) == reactions[0]):
                    await reaction.remove(self.ctx.author)
                    counter = 0
                    await self.msg.edit(embed=self.createEmbed(data,counter))
                if (str(reaction.emoji) == reactions[1]):
                    await reaction.remove(self.ctx.author)
                    if (counter > 0):
                        counter -= 1
                    await self.msg.edit(embed=self.createEmbed(data,counter))
                elif (str(reaction.emoji) == reactions[2]):
                    await reaction.remove(self.ctx.author)
                    await self.msg.delete()
                    selected = True
                    flag = 1
                elif (str(reaction.emoji) == reactions[3]):
                    await reaction.remove(self.ctx.author)
                    if (counter < data.__len__() - 1):
                        counter += 1
                    await self.msg.edit(embed=self.createEmbed(data,counter))
                elif (str(reaction.emoji) == reactions[4]):
                    await reaction.remove(self.ctx.author)
                    counter = data.__len__() - 1 
                    await self.msg.edit(embed=self.createEmbed(data,counter))
                elif (str(reaction.emoji) == reactions[5]):
                    await reaction.remove(self.ctx.author)
                    await self.msg.delete()
                    flag = 1
        if selected == True:
            return c.ARKServer.fromJSON(data[counter][4])
        else:
            return ''

class NotitifcationSelector():
    def __init__(self,ctx,bot,lang):
        self.ctx = ctx
        self.bot = bot
        self.l = lang # classes.Translation 
        pass

    async def select(self):
        reactions = ['1\N{variation selector-16}\N{combining enclosing keycap}','2\N{variation selector-16}\N{combining enclosing keycap}','3\N{variation selector-16}\N{combining enclosing keycap}','\u23F9']
        time = datetime.datetime(2000,1,1,0,0,0,0)
        embed = discord.Embed(title='Select notification type',description='Bot will send notifications to this channel\n \u200b',timestamp=time.utcnow())
        embed.set_footer(text='Bot v0.1 • Ping me to get prefix!')
        embed.add_field(name=':one: Server went offline',value='\u200b\u200b\u200b\u200b',inline=False)
        embed.add_field(name=':two: Server went online',value='\u200b\u200b\u200b\u200b',inline=False)
        embed.add_field(name=':three: Server went online/offline',value='\u200b\u200b\u200b\u200b',inline=False)
        self.msg = await self.ctx.send(embed=embed)
        for reaction in reactions:
            await self.msg.add_reaction(reaction)
        flag = 0
        while flag == 0:
            try:
                reaction,user = await self.bot.wait_for('reaction_add',timeout=100,check=lambda r,user: user != self.bot.user and r.message.id == self.msg.id)
            except asyncio.TimeoutError:
                flag = 1
                await self.msg.delete()
            else :
                if (str(reaction.emoji) == reactions[0]):
                    await self.msg.delete()
                    return 1
                if (str(reaction.emoji) == reactions[1]):
                    await self.msg.delete()
                    return 2
                elif (str(reaction.emoji) == reactions[2]):
                    await self.msg.delete()
                    return 3
                elif (str(reaction.emoji) == reactions[3]):
                    await self.msg.delete()
                    flag = 1
                    return 0

        
