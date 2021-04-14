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
import asyncio
import aiohttp 

class Updater(commands.Cog):
    '''
    Updates record for server in DB
    '''
    def __init__(self, bot):
        self.bot = bot
        self.cfg = config.Config()
        self.workersCount = self.cfg.workersCount # count of concurrent functions to tun
        self.server_list = [] #list of lists : [[server_id,server_status]...]
        print('Init')
        self.printer.start()
        self.t = c.Translation()

    async def initPool(self):
        '''
        init a pool of sql connections to DB
        '''
        #print('Started initing pool')
        #cfg = config.Config()
        #self.pool = await aiomysql.create_pool(host=cfg.dbHost, port=3306,
        #                              user=cfg.dbUser, password=cfg.dbPass,
        #                              db=cfg.DB, loop=asyncio.get_running_loop(), minsize=self.workersCount)
        print('Done initing pool (stub)!')

    async def makeAsyncRequest(self,SQL, params=()):
        return await makeAsyncRequest(SQL,params)

    async def makeAsyncRequestOld(self,SQL, params=()):
        '''
        Async method to make SQL requests using connections from pool inited in initPool()
        '''
        conn = await self.pool.acquire() # acquire one connecton from the pool
        async with conn.cursor() as cur: # with cursor as cur
            await cur.execute(SQL,params) # execute SQL with parameters
            result = await cur.fetchall() # fetch all results  
            await conn.commit() # commit changes
        self.pool.release(conn) # release current connection to the pool
        return result # return result

    def cog_unload(self): # on unload
        self.printer.cancel() # cancel the task 
        self.pool.terminate() # terminate pool of connections

    async def server_notificator(self,server):
        '''
        Function to notify about server events like server went up or down 
        '''
        #print('entered message sender')
        channels = self.notificationsList # all notification records
        channels = list(filter(lambda x:str(server[0]) in [i.strip() for i in x[4][1:-1].split(',')],self.notificationsList)) # find any channels that must receive notifications ????
        if (channels.__len__() <= 0): # if we have no channels to send notifications to
            return # return
        print(f'Found a notification record for {server[0]} server!')
        if (server[1] == 1 ): # if server went online
            ARKServer = server[2] # get server object
            for channel in channels: # for each channel we got from DB
                discordChannel = self.bot.get_channel(channel[1]) # get that channel
                if (discordChannel == None): # if channel not found
                    print(f'Channel not found for server : {server[0]} Channel id :{channel[1]}') # debug it
                    continue # and continue
                else: # if channel is found
                    aliases = await getAlias(0,discordChannel.guild.id,ARKServer.ip) # get an alias for that server
                    if (aliases == ''): # if no alias exist
                        name = await stripVersion(ARKServer) # name is striped name 
                    else:
                        name = aliases # else name is server's alias 
                    await discordChannel.send(f'Server {name} ({ARKServer.map}) went online!') # send notification
                    print(f'sent message for went online for server {server[0]}')
        if (server[1] == 2): # if server went offline
            ARKServer = server[2] # get server object (taken from DB)
            for channel in channels: # for each channel we need to send notification to 
                if (channel[3] == 1): # if we already sent notification (I wander how this would happen?)
                    continue
                discordChannel = self.bot.get_channel(channel[1]) # get channel stored in DB
                if (discordChannel == None): # if channel is not found
                    print(f'Channel not found for server : {server[0]} Channel id :{channel[1]}') # debug it
                    continue # and continue
                else:
                    aliases = await getAlias(0,discordChannel.guild.id,ARKServer.ip)
                    if (aliases == ''):
                        name = ARKServer.name.find(f'- ({ARKServer.version})')
                        name = ARKServer.name[:name].strip()
                    else:
                        name = aliases
                    await discordChannel.send(f'Server {name} ({ARKServer.map}) went offline!')
                    print(f'sent message for went offline for server {server[0]}')
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
        #print('Entered notificator!')
        for server in serverList:
            await self.server_notificator(server)
            #print(f'Sent server notifications for server : {server[0]}!')
            #player_notificator()

    async def update_server(self,serverId): # universal server upgrader 
        server = list(filter(lambda x:x[0] == serverId,self.servers)) # select from local cache (self.servers)
        server = server[0] # select first result 
        ip = server[1] # get server's ip
        result = []
        try: # standart online/offline check 
            serverObj = await c.ARKServer(ip).AGetInfo() # get info about server 
            playersList = await c.PlayersList(ip).AgetPlayersList() # get players list
            if (not hasattr(c.ARKServer.fromJSON(server[4]), 'battleURL') and bool(server[6])): # if we don't have battle url already and server is online
                #print(f'We don`t have battle URl for server {ip} {getattr(c.ARKServer.fromJSON(server[4]),"battleURL","nothing")}')
                battleURL = await self.battleAPI.getBattlemetricsUrl(serverObj) # get it
                if (battleURL): # if we getched the url
                    serverObj.battleURL = battleURL # put it in
            await makeAsyncRequest('UPDATE servers SET ServerObj=%s , PlayersObj=%s , LastOnline=1 , OfflineTrys=0 WHERE Ip =%s',(serverObj.toJSON(),playersList.toJSON(),ip)) # update DB record
            if (bool(server[6]) == False): # if previously server was offline (check LastOnline column)
                result = [1,serverObj,playersList,0] # return server went online (return status 1 and two new objects)
            else:
                result = [3,serverObj,playersList,0] # return unchanged (return status 3 and two new objects)
        except c.ARKServerError as error: # catch my own error 
            if (type(error) != c.ARKServerError): # if not my error 
                errors = traceback.format_exception(type(error), error, error.__traceback__)
                errors_str = ''.join(errors)
                date = datetime.utcfromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S')
                ip = await makeAsyncRequest('SELECT Ip FROM servers WHERE Id=%s',(server[0],))
                await sendToMe(f'{errors_str}\nDate: {date}\n Server id: {server[0]}\nServer ip:{ip[0][0]}',self.bot)
                result = [1,c.ARKServer('1.1.1.1:1234'),c.PlayersList('1.1.1.1:1234')]
            await makeAsyncRequest('UPDATE servers SET LastOnline=0,OfflineTrys=%s WHERE Ip=%s',(server[7]+1,ip,)) # update DB (add one to OfflineTrys and set LastOnline to 0)
            if (bool(server[6]) == True): # if server was online
                result = [2,c.ARKServer.fromJSON(server[4]),c.PlayersList.fromJSON(server[5]),server[7]+1] #return server went offline
            else:
                result = [3,c.ARKServer.fromJSON(server[4]),c.PlayersList.fromJSON(server[5]),server[7]+1] #return unchanged
        # change in notifications : send them as soon as possible so updates would be faster
        await self.server_notificator(result) # send notifications 
        return result

    @tasks.loop(seconds=120.0)
    async def printer(self): #entrypoint
        await sendToMe('Entered updater!',self.bot) # debug
        start = time.perf_counter() # start timer
        chunksTime = [] # list to old time it takes to process each chunk
        self.notificationsList = await makeAsyncRequest('SELECT * FROM notifications WHERE Type=3') # fetch all notifications records
        self.servers = await makeAsyncRequest('SELECT * FROM servers') # fetch all servers (it must be heavy ?)
        serverCount = self.servers.__len__() # get current count of servers
        try:
            print('Entered updater!') # debug
            servers = self.servers 
            server_list = [] # empty list
            for i in range(1,serverCount - self.workersCount,self.workersCount): # from 1 to server count with step of number of workers 
                localStart = time.perf_counter()
                #print(f'Updating servers: {[server[0] for server in  servers[i:i+self.workersCount]]}') # debug
                tasks = [self.update_server(i[0]) for i in servers[i:i+self.workersCount]] # generate tasks to complete (update servers)
                results = await asyncio.gather(*tasks) # run all generated tasks in paralel 
                a = 0 # in stead of traditional i lol 
                for result in results: # loop throuh results
                    server_list.append([servers[i+a][0],result[0],result[1],result[2]]) # append to server list it id,and result from update function (status, two object and offlinetrys)
                    a += 1
                localEnd = time.perf_counter()
                chunksTime.append(localEnd - localStart)
            #if (self.bot.is_ready()): # if bot's cache is ready
            #    print('handling notifications') # handle notifictaions
            #    updater_end = time.perf_counter()
            #    await self.notificator(server_list) # pass the list with servers and their statuses to the function
            #    end = time.perf_counter() # end performance timer
            #    await sendToMe(f'It took {updater_end - start:.4f} seconds to update all servers!\n{end - updater_end:.4f} sec. to send all notifications.\n{end - start:.4f} sec. in total',self.bot) # debug
            #else: # if not
            end = time.perf_counter() # end performance timer
            await sendToMe(f"It took {end - start:.4f} seconds to update all servers!\nNotifications weren`t sent because bot isn't ready\n{end - start:.4f} sec. in total",self.bot) # debug
            await sendToMe(f'Max chunk time is: {max(chunksTime):.4f}\nMin chunk time: {min(chunksTime):.4f}\nAverage time is:{sum(chunksTime)/len(chunksTime):.4f}\nChunk lenth is: {self.workersCount}\nUpdate queue lenth is: {self.servers.__len__()}',self.bot)
        except KeyError as error:
            await self.on_error(error)
            #await deleteServer(server[1])
        except BaseException as error: # if any exception
            await self.on_error(error)
            
    #@printer.error
    async def on_error(self,error):
        errors = traceback.format_exception(type(error), error, error.__traceback__)
        time = int(time.time())
        date = datetime.utcfromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
        errors_str = ''.join(errors)
        message = f'Error in updater loop!\n It happend at `{date}`\n```{errors_str}```'
        if (errors_str >= 2000):
            try:
                await sendToMe(message[:1975] + '`\nEnd of first part',self.bot)
                await sendToMe(message[1975:-1],self.bot)
            except BaseException as e:
                await sendToMe('Lenth of error message is over 4k!',self.bot)
                await sendToMe(e,self.bot)

    @printer.before_loop
    async def before_printer(self):
        print('waiting...')
        # await self.bot.wait_until_ready() why waiste all this time when we can update DB while cache is updating? 
        self.session = aiohttp.ClientSession() # get aiohttps's session 
        self.battleAPI = c.BattleMetricsAPI(self.session) # contrict API class 
        await self.initPool()
        print('done waiting')



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

