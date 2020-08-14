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
import notifications
import io
import traceback
from deepdiff import DeepDiff
import datetime
from server_cmd import *

debug = Debuger('updater') # create debuger (see helpers.py)
conf = config.Config() # load config
game = discord.Game('ping me to get prefix')
bot = commands.Bot(command_prefix=get_prefix,help_command=None,activity=game) # create bot with default prefix and no help command
debug.debug('Inited DB and Bot!') # debug into console !
t = c.Translation() # load default english translation

bot.loop.set_debug(conf.debug)

class Updater(commands.Cog):
    def __init__(self, bot):
        self.index = 0
        self.bot = bot
        self.printer.start()

    def cog_unload(self):
        self.printer.cancel()

    async def playersCheck(self,ip,Id,playersList):
        time = datetime.datetime(2000,1,1,0,0,0,0) # contrict this time because python
        server = makeRequest("SELECT PlayersObj,ServerObj,Id FROM servers WHERE Id=%s",(Id,)) # select previos players list and server info and Id 
        notifications = makeRequest("SELECT * FROM notifications WHERE Type=123") # select all notifications 
        for record in notifications: # for each record
            guild = makeRequest('SELECT * FROM settings WHERE GuildId=%s',(record[5],)) # select settings of guild in record 
            if (Id not in json.loads(guild[0][3])): # if server id not in json decoded array 
                continue # return
            if (notifications.__len__() > 0):
                channelId = record[1]
            else:
                continue
            playersObj = c.ARKServer.fromJSON(server[0][0])
            serverObj = c.ARKServer.fromJSON(server[0][1])
            test = DeepDiff(playersObj, playersList, view='tree')
            print('Main obj')
            print(test)
            if ('iterable_item_removed' in test):
                left = test['iterable_item_removed']
                print('left')
                print(left)
                for entry in left:
                    print(entry.t1)
                    print(entry)
                    print(f'Player {entry.t1.name} left')
                    channel = bot.get_channel(channelId)
                    #await channel.send(f'Player {entry.t1.name} left {serverObj.name} ({serverObj.ip})!')
            else:
                print('Noone left')
            if ('iterable_item_added' in test):
                joined = test['iterable_item_added']
                print('joined')
                print(joined)        
                for entry in joined:
                    if (entry.t2.name != '(unknown player)'):
                        print(entry.t2)
                        print(entry)
                        channel = bot.get_channel(channelId)
                        await channel.send(f'Player {entry.t2.name} joined {serverObj.name} ({serverObj.ip})!')
            else:
                print('Noone joined')

            if ('values_changed' in test):
                joined = test['values_changed']
                print('changed')
                print(joined)        
                for entry in joined:
                    if (entry.t1 == '(unknown player)'):
                        print(f'Player {entry.t2} joined')
                        channel = bot.get_channel(channelId)
                        await channel.send(f'Player {entry.t2} joined {serverObj.name} ({serverObj.ip})!')
                    print(entry.t2)
                    print(entry)
            else:
                print('notheing changed')

    async def updateMessage(self,Id,server,players):
        messages = makeRequest('SELECT * FROM notifications WHERE Type=124 AND ServersIds=%s',(str(Id),))
        embedMaker = ServerCmd(self.bot)
        for message in messages:
            channel = self.bot.get_channel(message[1])
            messageToUpdate = await channel.fetch_message(int(message[5]))
            embed = embedMaker.serverInfo(server,players,True)
            await messageToUpdate.edit(content=embed)

    @tasks.loop(seconds=30.0)
    async def printer(self):
        try:
            servers = makeRequest('SELECT * FROM servers') #get all servers
            notifications = makeRequest('SELECT * FROM notifications') # get all notifications
            serverList = [] # will be filled with content [['server_ip',server_online(1 or 0)],...]
            for server in servers: # for each server
                ip = server[1] # get it ip
                id = server[0] # get it id
                try: # standart online/offline check
                    serverObj = c.ARKServer(ip).GetInfo() # get info about server 
                    playersList = c.PlayersList(ip).getPlayersList() # get players list
                    await self.playersCheck(ip,id,playersList) # fucked part begins pass to it ip and id of current server as well as list of players that we got now
                    await self.updateMessage(id,serverObj,playersList)
                    makeRequest('UPDATE servers SET ServerObj=%s , PlayersObj=%s , LastOnline=1 WHERE Ip =%s',(serverObj.toJSON(),playersList.toJSON(),ip)) # update DB record
                    test = [] # ['server_ip',server_online(1 or 0)]
                    test.append(id) # append server id
                    if (server[6] == 0):
                        test.append(1) # append 1 for offline server status
                    else:
                        test.append(3) # fast fix to logic problem (if server was online on past check we don't need to notify user)
                    serverList.append(test) # append our mini list to our main list
                    print(f'Updated record for online server: {ip}') # debug
                    
                except BaseException as e: # if server not online (will throw socket.timeout but I lazy) 
                    traceback.print_last()
                    print(e)
                    test = [] # make our mini list
                    test.append(id) # append server id
                    if (server[6] == 1):
                        test.append(0) # append 1 for offline server status
                    else:
                        test.append(3) # fast fix to logic problem (if server was offline on past check we don't need to notify user)
                    serverList.append(test) # append our mini list to main list
                    makeRequest('UPDATE servers SET LastOnline=0, OfflineTrys=%s  WHERE Ip =%s',(server[6]+1,ip)) # update server
                    print(f'Updated record for offline server: {ip}') # debug
            
            for server in serverList: # process our main list 
                break
                # for each server record 
                for record in notifications: # go throu all notifications
                    idsList = json.loads(record[4]) # load list of server ids in notification record
                    if server[0] in idsList: # if we found our current server id in list
                        if 1 == record[2] or 3 == record[2] and server[1] == 0 and record[3] == 0: # if we found 1 (id for server went offline notification) AND server status in main list is 0 (offline) AND we didn't sent message already (sent row in DB) 
                            channel = bot.get_channel(record[1]) # get channel id from notification record
                            serverRecord = makeRequest('SELECT * FROM servers WHERE Id=%s',(server[0],)) # get server record for that ip
                            await channel.send(f'Server {serverRecord[0][1]} went down !') # send channel with server ip (server record will be used to get server name) 
                            makeRequest('UPDATE notifications SET Sent=1 WHERE Id=%s',(record[0],)) # update notification record (set sent row to 1 it will be resetted later)
                        if 2 == record[2] or 3 == record[2]  and server[1] == 1 and record[3] == 0: # if we found 2 (id for server went online notification) AND server status in main list is 1 (online) AND we didn't sent message already (sent row in DB) 
                            channel = bot.get_channel(record[1]) # get channel id from notification record
                            serverRecord = makeRequest('SELECT * FROM servers WHERE Id=%s',(server[0],)) # get server record for that ip
                            await channel.send(f'Server {serverRecord[0][1]} went up !') # send channel with server ip (server record will be used to get server name) 
                            makeRequest('UPDATE notifications SET Sent=1 WHERE Id=%s',(record[0],)) # update notification record (set sent row to 1 it will be resetted later)
        except BaseException as e:
            print(notifications)
            print(e)
            print(traceback.format_exc())

    @tasks.loop(seconds=60.0)
    async def resetter(self):
        makeRequest('UPDATE notifications SET Sent=0 WHERE Sent=1')
    
bot.add_cog(Updater(bot))

bot.run(conf.token)


