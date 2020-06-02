import discord
from discord.ext import tasks, commands
from helpers import *
import classes as c

class Updater(commands.Cog):
    def __init__(self):
        self.index = 0
        self.update.start()

    def cog_unload(self):
        self.update.cancel()

    @tasks.loop(seconds=60*1)
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
                    makeRequest('UPDATE Servers SET ServerObj=?, DataObj=? WHERE IP=?',[server.toJSON(),playersList.toJSON(),ip]) # update it
                except Exception as e: # if any exception
                    debug.debug(e) # debug
                    debug.debug(f'Server {ip} is offline!') # also debug
                    OfflineTrys = makeRequest('SELECT * FROM Servers WHERE IP = ?',[ip])
                    OfflineTrys = OfflineTrys[0][4]
                    makeRequest('UPDATE Servers SET LastOnline=?, OfflineTrys=? WHERE IP=?',[0,OfflineTrys+1,ip]) # update it


                
