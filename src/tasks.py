import discord
from discord.ext import tasks, commands
from helpers import *
import classes as c

class Updater(commands.Cog): 
    def on_error(self,error):
        print(error)

    def __init__(self,bot):
        self.bot = bot
        self.update.start()

    def cog_unload(self):
        self.update.cancel()



    @tasks.loop(seconds=60*5)
    async def update(self):
        debug = Debuger('Update_DB_Task')
        debug.debug('Entered task!')
        data = makeRequest('SELECT * FROM Servers')
        if (data.__len__() <= 0):
            debug.debug('No DB records!')
            return
        for server in data:
            ip = server[5]
            if IpCheck(ip) == False:
                debug.debug(f'Ip {ip} is incorrect! Dropping record!')
                makeRequest('DELETE FROM Servers WHERE IP = ?',[ip])
            else :
                try: 
                    server = c.ARKServer(ip) # construct our classes
                    playersList = c.PlayersList(ip)
                    playersList.getPlayersList() # and get data
                    server.GetInfo()
                    debug.debug(f"Server {ip} is up!") # and debug
                    makeRequest('UPDATE Servers SET ServerObj=?, DataObj=?,LastOnline=1,OfflineTrys=0  WHERE IP=?',[server.toJSON(),playersList.toJSON(),ip]) # update it
                    notifications = makeRequest('SELECT * FROM notifications WHERE Ip = ? AND Sent = 1',[ip])
                    if (notifications.__len__() > 0):
                        for notification in notifications:
                            id = notification[2]
                            await  self.bot.wait_until_ready()
                            channel =  self.bot.get_channel(int(id))
                            await channel.send(f'Server {ip} is up now!')
                            makeRequest('UPDATE notifications SET Sent = 0 WHERE Ip = ?',[ip]) # and update all records to say that we sent message
                except Exception as e: # if any exception
                    debug.debug(e) # debug
                    debug.debug(f'Server {ip} is offline!') # also debug
                    OfflineTrys = makeRequest('SELECT * FROM Servers WHERE IP = ?',[ip])
                    OfflineTrys = OfflineTrys[0][4] # get offline trys
                    makeRequest('UPDATE Servers SET LastOnline=?, OfflineTrys=? WHERE IP=?',[0,OfflineTrys+1,ip]) # update it
                    users = makeRequest('SELECT * FROM notifications WHERE Ip = ? AND Sent = 0 OR Sent = NULL',[ip]) # get all subscribed users
                    for user in users:
                        id = user[2]
                        debug.debug(type(self.bot))
                        await  self.bot.wait_until_ready()
                        channel =  self.bot.get_channel(int(id))
                        await channel.send(f'Server {ip} is down!')
                    makeRequest('UPDATE notifications SET Sent = 1 WHERE Ip = ?',[ip]) # and update all records to say that we sent message

#    @update.error()
#    async def error(self,error):
#        print(error)

    