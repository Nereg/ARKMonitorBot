import classes as c # our classes
from helpers import * # our helpers
import config  # config
import discord # main discord libary
from discord.ext import commands # import commands extension
from discord.ext import tasks
import json 
import traceback
import time
from datetime import datetime
import dbl
import os 
import io
import traceback
import socket
import menus as m
import concurrent.futures._base as base

#debug = Debuger('updater') # create debuger (see helpers.py)
#conf = config.Config() # load config
#game = discord.Game('ping me to get prefix')
#bot = commands.Bot(command_prefix=get_prefix,help_command=None,activity=game) # create bot with default prefix and no help command
#debug.debug('Inited DB and Bot!') # debug into console !
#t = c.Translation() # load default english translation

#bot.loop.set_debug(conf.debug)

class Updater(commands.Cog):
    def __init__(self, bot):
        self.index = 0
        self.bot = bot
        #self.printer.start()
        self.server_list = [] #list of lists : [[server_id,server_status]...]
        print('Init')
        self.printer.start()
        self.t = c.Translation()
        # 1 - went online 
        # 2 - went offline
        # 3 - unchanged

    def cog_unload(self):
        self.printer.cancel()

    async def server_notificator(self,server):
        print('entered message sender')
        if (server[1] == 1 ): # server went online
            channels = makeRequest('SELECT * FROM notifications WHERE ServersIds LIKE %s AND Type=3',(f'%{server[0]}%',))
            if (channels.__len__() >= 1):
                server = server[2]
                for channel in channels:
                    discordChannel = self.bot.get_channel(channel[1])
                    if (discordChannel == None):
                        print(f'Channel not found! Channel id :{channel[1]}')
                    else:
                        await discordChannel.send(f'Server {server.name} ({server.map}) ({server.ip}) went online!')
                        print('sent message for went online')
        if (server[1] == 2 ): # server went online
            channels = makeRequest('SELECT * FROM notifications WHERE ServersIds LIKE %s AND Type=3',(f'%{server[0]}%',))
            if (channels.__len__() >= 1):
                server = server[2]
                for channel in channels:
                    discordChannel = self.bot.get_channel(channel[1])
                    if (discordChannel == None):
                        print(f'Channel not found! Channel id :{channel[1]}')
                    else:
                        await discordChannel.send(f'Server {server.name} ({server.map}) ({server.ip}) went offline!')
                        print('sent message for went online')


    async def notificator(self,serverList):
        for server in serverList:
            if (server[1] != 3): #################################
                print('sent server notifications')
                await self.server_notificator(server)
            #player_notificator()

    async def update_server(self,serverId):
        server = makeRequest('SELECT * FROM servers WHERE Id=%s',(serverId,)) #get current server
        server = server[0]
        ip = server[1]
        try:
            serverObj = await c.ARKServer(ip).AGetInfo() # get info about server 
            playersList = await c.PlayersList(ip).AgetPlayersList() # get players list
            makeRequest('UPDATE servers SET ServerObj=%s , PlayersObj=%s , LastOnline=1 WHERE Ip =%s',(serverObj.toJSON(),playersList.toJSON(),ip)) # update DB record
            if (bool(server[6]) == False): # if previously server was offline 
                return [1,serverObj,playersList] # return server went online
            else:
                return [3,serverObj,playersList] # return unchanged
        except BaseException as error:
            if (type(error) != base.TimeoutError):
                meUser = self.bot.get_user(277490576159408128)
                meDM = await meUser.create_dm()
                errors = traceback.format_exception(type(error), error, error.__traceback__)
                errors_str = ''.join(errors)
                date = datetime.utcfromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S')
                await meDM.send(f'{errors_str}\nDate: {date}\n Server id: {server[0]}')
            print('123123123')
            print(error)
            makeRequest('UPDATE servers SET LastOnline=0 WHERE Ip=%s',(ip,)) # update DB
            if (bool(server[6]) == True): # if server was online
                return [2,c.ARKServer.fromJSON(server[4]),c.PlayersList.fromJSON(server[5])] #return server went offline
            else:
                return [3,c.ARKServer.fromJSON(server[4]),c.PlayersList.fromJSON(server[5])] # return unchanged

    @tasks.loop(seconds=30.0)
    async def printer(self):
        try:
            print('Entered updater!')
            servers = makeRequest('SELECT * FROM servers')
            server_list = []
            for server in servers:
                print(f'Updating server {server[0]}')
                result = await self.update_server(server[0])
                server_list.append([server[0],result[0],result[1],result[2]])
                print(f'Updated server! Result is {result}')
            print(server_list)
            print('handling notifications')
            await self.notificator(server_list)
        except BaseException as e:
            print(e)
            print(traceback.format_exc())

    @printer.before_loop
    async def before_printer(self):
        print('waiting...')
        await self.bot.wait_until_ready()

    @commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True)
    @commands.command()
    async def watch(self,ctx):
        selector = m.Selector(ctx,self.bot,self.t)
        server = await selector.select()        
        if server == '':
            return
        Type = 3
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

    @commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True)
    @commands.command()
    async def unwatch(self,ctx):
        selector = m.Selector(ctx,self.bot,self.t)
        server = await selector.select()        
        if server == '':
            return
        ip = server.ip
        serverId = makeRequest('SELECT Id FROM servers WHERE Ip=%s',(ip,))[0][0]
        notifications = makeRequest('SELECT * FROM notifications WHERE DiscordChannelId=%s AND Type=3 AND ServersIds LIKE %s',(ctx.channel.id, f'%{serverId}%',))
        if (notifications.__len__() <= 0):
            await ctx.send('You is not subscribed to that server!')
            return
        else:
            newServerlist = json.loads(notifications[0][4])
            newServerlist.remove(serverId)
            newServerlist = json.dumps(newServerlist)
            makeRequest('UPDATE notifications SET ServersIds=%s WHERE Id=%s',(newServerlist,notifications[0][0]))
            await ctx.send('Done !')
def setup(bot):
    bot.add_cog(Updater(bot))

