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
        #self.resetter.start()
        self.t = c.Translation()
        # 1 - went online 
        # 2 - went offline
        # 3 - unchanged

    async def initPool(self):
        print('Started initing pool')
        cfg = config.Config()
        self.pool = await aiomysql.create_pool(host=cfg.dbHost, port=3306,
                                      user=cfg.dbUser, password=cfg.dbPass,
                                      db=cfg.DB, loop=asyncio.get_running_loop(), minsize=2)
        print('Done initing pool!')

    async def makeAsyncRequest(self,SQL, params=()):
        conn = await self.pool.acquire()
        async with conn.cursor() as cur:
            await cur.execute(SQL,params)
            result = await cur.fetchall()
            await conn.commit()
        self.pool.release(conn)
        return result

    def cog_unload(self):
        self.printer.cancel()
        self.pool.terminate()

    async def server_notificator(self,server):
        #print('entered message sender')
        #print(server)
        channels = self.notificationsList
        channels = list(filter(lambda x:str(server[0]) in [i.strip() for i in x[4][1:-1].split(',')],self.notificationsList))
        #print('channels')
        #print(channels)
        if (channels.__len__() <= 0):
            return
        #db_server = await makeAsyncRequest('SELECT OfflineTrys FROM servers WHERE Id=%s',(server[0],))
        if (server[1] == 1 ): # server went online
            ARKServer = server[2]
            for channel in channels:
                discordChannel = self.bot.get_channel(channel[1])
                if (discordChannel == None):
                    continue
                    #print(f'Channel not found for server : {server[0]} Channel id :{channel[1]}')
                else:
                    aliases = await getAlias(0,discordChannel.guild.id,ARKServer.ip)
                    if (aliases == ''):
                        name = ARKServer.name.find(f'- ({ARKServer.version})')
                        name = ARKServer.name[:name].strip()
                    else:
                        name = aliases
                    await discordChannel.send(f'Server {name} ({ARKServer.map}) went online!')
                    #print(f'sent message for went online for server {server[0]}')
        if (server[1] == 2): # may be fucked up sometimes but it won't notify servial times 
            ARKServer = server[2]
            for channel in channels:
                if (channel[3] == 1):
                    break
                discordChannel = self.bot.get_channel(channel[1])
                if (discordChannel == None):
                    continue
                    #print(f'Channel not found for server : {server[0]} Channel id :{channel[1]}')
                else:
                    aliases = await getAlias(0,discordChannel.guild.id,ARKServer.ip)
                    if (aliases == ''):
                        name = ARKServer.name.find(f'- ({ARKServer.version})')
                        name = ARKServer.name[:name].strip()
                    else:
                        name = aliases
                    await discordChannel.send(f'Server {name} ({ARKServer.map}) went offline!')
                    #print(f'sent message for went offline for server {server[0]}')
                    await makeAsyncRequest('UPDATE notifications SET Sent=1 WHERE Id=%s',(channel[0],))

        #if (server[1] == 2 ): # server went offline
        #    db_server = makeRequest('SELECT OfflineTrys FROM servers WHERE Id=%s',(server[0],))
        #    channels = makeRequest('SELECT * FROM notifications WHERE ServersIds LIKE %s AND Type=3',(f'%{server[0]}%',))
        #    if (channels.__len__() >= 1):
        #        ARKServer = server[2]
        #        for channel in channels:
        #            discordChannel = self.bot.get_channel(channel[1])
        #            if (discordChannel == None):
        #                print(f'Channel not found! Channel id :{channel[1]}')
        #            else:
        #                await discordChannel.send(f'Server {ARKServer.name} ({ARKServer.map}) ({ARKServer.ip}) went offline!')
        #                print('sent message for went offline')


    async def notificator(self,serverList):
        print('Entered notificator!')
        for server in serverList:
            await self.server_notificator(server)
            print(f'Sent server notifications for server : {server[0]}!')
            #player_notificator()

    async def update_server(self,serverId): # universal server upgrader 
        #server = makeRequest('SELECT * FROM servers WHERE Id=%s',(serverId,)) #get current server
        #server = server[0] # set var to first found result
        server = list(filter(lambda x:x[0] == serverId,self.servers))
        server = server[0]
        ip = server[1] # get server's ip
        try: # standart online/offline check 
            serverObj = await c.ARKServer(ip).AGetInfo() # get info about server 
            playersList = await c.PlayersList(ip).AgetPlayersList() # get players list
            await makeAsyncRequest('UPDATE servers SET ServerObj=%s , PlayersObj=%s , LastOnline=1 , OfflineTrys=0 WHERE Ip =%s',(serverObj.toJSON(),playersList.toJSON(),ip)) # update DB record
            if (bool(server[6]) == False): # if previously server was offline (check LastOnline column)
                return [1,serverObj,playersList,0] # return server went online (return status 1 and two new objects)
            else:
                return [3,serverObj,playersList,0] # return unchanged (return status 3 and two new objects)
        except c.ARKServerError as error: # catch my own error 
            if (type(error) != c.ARKServerError): # if not my error 
                meUser = self.bot.get_user(277490576159408128) # log it
                meDM = await meUser.create_dm()
                errors = traceback.format_exception(type(error), error, error.__traceback__)
                errors_str = ''.join(errors)
                date = datetime.utcfromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S')
                ip = await makeAsyncRequest('SELECT Ip FROM servers WHERE Id=%s',(server[0],))
                await meDM.send(f'{errors_str}\nDate: {date}\n Server id: {server[0]}\nServer ip:{ip[0][0]}')
            #print('123123123') # debug
            #errors = traceback.format_exception(type(error), error, error.__traceback__)
            #errors_str = ''.join(errors)
            #print(errors_str)
            await makeAsyncRequest('UPDATE servers SET LastOnline=0,OfflineTrys=%s WHERE Ip=%s',(server[7]+1,ip,)) # update DB
            if (bool(server[6]) == True): # if server was online
                return [2,c.ARKServer.fromJSON(server[4]),c.PlayersList.fromJSON(server[5]),server[7]+1] #return server went offline
            else:
                return [3,c.ARKServer.fromJSON(server[4]),c.PlayersList.fromJSON(server[5]),server[7]+1] # return unchanged

    @tasks.loop(seconds=120.0)
    async def printer(self): #entrypoint
        await sendToMe('Entered updater!',self.bot)
        start = time.perf_counter()
        self.notificationsList = await makeAsyncRequest('SELECT * FROM notifications WHERE Type=3')
        self.servers = await makeAsyncRequest('SELECT * FROM servers')
        try:
            print('Entered updater!') # debug
            servers = self.servers
            server_list = [] # empty list
            for server in servers: # for server in servers
                print(f'Updating server {server[0]}') # debug
                result = await self.update_server(server[0]) # update server
                server_list.append([server[0],result[0],result[1],result[2]]) # append to server list it id,and result from update function (status, two object and offlinetrys)
                #print(f'Updated server! Result is {result}')
            #print(server_list)
            print('handling notifications')
            await self.notificator(server_list)
            end = time.perf_counter()
            await sendToMe(f'It took {end - start} seconds to update all servers!',self.bot)
        except KeyError:
            await deleteServer(server[1])
        except BaseException as e: # if any exception
            print(server)
            print(e)
            print(traceback.format_exc()) # print it

    @printer.before_loop
    async def before_printer(self):
        print('waiting...')
        await self.bot.wait_until_ready()
        await self.initPool()
        print('done waiting')

    #@tasks.loop(seconds=60.0)
    #async def resetter(self):
    #    await makeAsyncRequest('UPDATE notifications SET Sent = 0')

    @commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True)
    @commands.command()
    async def watch(self,ctx):
        selector = m.Selector(ctx,self.bot,self.t)
        server = await selector.select()        
        if server == '':
            return
        Type = 3
        ip = server.ip
        serverId = await makeAsyncRequest('SELECT Id FROM servers WHERE Ip=%s',(ip,))
        serverId = serverId[0][0]
        notifications2 = await makeAsyncRequest('SELECT * FROM notifications WHERE DiscordChannelId=%s',(ctx.channel.id,))
        notifications = await makeAsyncRequest('SELECT * FROM notifications WHERE DiscordChannelId=%s AND Type=%s',(ctx.channel.id,Type,))
        if (notifications.__len__() <= 0):
            ids = []
            ids.append(serverId)
            await makeAsyncRequest('INSERT INTO `notifications`(`DiscordChannelId`, `ServersIds`, `Data`, `Sent`, `Type`) VALUES (%s,%s,"{}",0,%s)',(ctx.channel.id,json.dumps(ids),Type,))
            await ctx.send(self.t.l['done'])
            return
        else:
            ids = json.loads(notifications[0][4])
            if serverId in ids:
                await ctx.send('You already receive notifications about this server!')
                return
            else:
                ids.append(serverId)
                await makeAsyncRequest('UPDATE notifications SET ServersIds=%s WHERE DiscordChannelId=%s AND Type=%s',(json.dumps(ids),ctx.channel.id,Type,))
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
        serverId = await makeAsyncRequest('SELECT Id FROM servers WHERE Ip=%s',(ip,))
        serverId = serverId[0][0]
        notifications = await makeAsyncRequest('SELECT * FROM notifications WHERE DiscordChannelId=%s AND Type=3 AND ServersIds LIKE %s',(ctx.channel.id, f'%{serverId}%',))
        if (notifications.__len__() <= 0):
            await ctx.send('You is not subscribed to that server!')
            return
        else:
            newServerlist = json.loads(notifications[0][4])
            newServerlist.remove(serverId)
            newServerlist = json.dumps(newServerlist)
            await makeAsyncRequest('UPDATE notifications SET ServersIds=%s WHERE Id=%s',(newServerlist,notifications[0][0]))
            await ctx.send('Done !')

def setup(bot):
    bot.add_cog(Updater(bot))

