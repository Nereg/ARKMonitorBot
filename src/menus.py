import discord
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

    async def createEmbed(self, data,number):
        server = c.ARKServer.fromJSON(data[number][4])
        online = bool(data[number][6])
        aliases = await getAlias(0,self.ctx.guild.id,server.ip)
        name = server.name if aliases == '' else aliases
        embed = discord.Embed(title=f'{number+1}. {name}',color=randomColor())
        status = ':green_circle: '+ self.l.l['online'] if online else ':red_circle: ' + self.l.l['offline']
        pve = self.l.l['yes'] if server.PVE else self.l.l['no']
        embed.add_field(name='IP',value=server.ip)
        embed.add_field(name=self.l.l['status'],value=status)
        embed.add_field(name=self.l.l['version'],value=f'{server.version}')
        embed.add_field(name='PVE?',value=pve)
        embed.add_field(name=self.l.l['players_count'],value=f'{server.online}/{server.maxPlayers}')
        embed.add_field(name='Map',value=server.map)
        return embed

    async def select(self):
        reactions = ['⏮️','\u2B05','\u2705','\u27A1','⏭️','\u23F9'] # array with buttons
        if self.ctx.guild == None :  # old code 
            GuildId = self.ctx.channel.id
            Type = 1
        else:
            GuildId = self.ctx.guild.id
            Type = 0
        data = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=%s AND Type=0',(GuildId,)) # select settings from DB
        if (data.__len__() == 0): # if no servers are added
            await self.ctx.send(self.l.l['no_servers_added'].format(self.ctx.prefix)) # send error message
            return '' # return 
        if (data[0][3] == None or data[0][3] == 'null' or data[0][3] == '[null]'): # if no servers are added 
            await self.ctx.send(self.l.l['no_servers_added'].format(self.ctx.prefix)) # send error message
            return '' # return
        else: # if we have servers added
            Servers = json.loads(data[0][3]) # load them
        statement = "SELECT * FROM servers WHERE Id IN ({})".format(', '.join(['{}'.format(Servers[i]) for i in range(len(Servers))]))
        print(statement)
        try:
            data = makeRequest(statement)
        except BaseException as e:
            await sendToMe(statement,self.bot,True)
            raise e
        try:
            self.msg = await self.ctx.send(self.l.l['server_select'],embed=await self.createEmbed(data,0))
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
                try:
                    await self.msg.clear_reactions()
                    await self.msg.edit(content='The interactive menu was closed.',embed=None)
                except discord.errors.NotFound: # It was SO ANNOYING ! DONT DELET MESSAGES THERE ARE STOP BUTTON!  
                    return
            else :
                if (str(reaction.emoji) == reactions[0]):
                    await reaction.remove(self.ctx.author)
                    counter = 0
                    await self.msg.edit(embed=await self.createEmbed(data,counter))
                if (str(reaction.emoji) == reactions[1]):
                    await reaction.remove(self.ctx.author)
                    if (counter > 0):
                        counter -= 1
                    await self.msg.edit(embed=await self.createEmbed(data,counter))
                elif (str(reaction.emoji) == reactions[2]):
                    await reaction.remove(self.ctx.author)
                    await self.msg.delete()
                    selected = True
                    flag = 1
                elif (str(reaction.emoji) == reactions[3]):
                    await reaction.remove(self.ctx.author)
                    if (counter < data.__len__() - 1):
                        counter += 1
                    await self.msg.edit(embed=await self.createEmbed(data,counter))
                elif (str(reaction.emoji) == reactions[4]):
                    await reaction.remove(self.ctx.author)
                    counter = data.__len__() - 1 
                    await self.msg.edit(embed=await self.createEmbed(data,counter))
                elif (str(reaction.emoji) == reactions[5]):
                    await reaction.remove(self.ctx.author)
                    await self.msg.delete()
                    flag = 1
        if selected == True:
            return c.ARKServer.fromJSON(data[counter][4])
        else:
            return ''