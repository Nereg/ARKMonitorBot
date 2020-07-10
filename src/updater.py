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

    @tasks.loop(seconds=30.0)
    async def printer(self):
        try:
            servers = makeRequest('SELECT * FROM servers')
            notifications = makeRequest('SELECT * FROM notifications')
            serverList = []
            for server in servers:
                ip = server[1]
                id = server[0]
                try:
                    serverObj = c.ARKServer(ip).GetInfo()
                    playersList = c.PlayersList(ip).getPlayersList()
                    makeRequest('UPDATE servers SET ServerObj=%s , PlayersObj=%s , LastOnline=1 WHERE Ip =%s',(serverObj.toJSON(),playersList.toJSON(),ip))
                    test = []
                    test.append(id) # append server id
                    test.append(1) # append 1 for online server status
                    serverList.append(test)
                    print(f'Updated record for online server: {ip}')
                except:
                    test = []
                    test.append(id) # append server id
                    test.append(0) # append 1 for offline server status
                    serverList.append(test)
                    makeRequest('UPDATE servers SET LastOnline=0, OfflineTrys=%s  WHERE Ip =%s',(server[6]+1,ip))
                    print(f'Updated record for offline server: {ip}')
            for server in serverList:
                for record in notifications:
                    idsList = json.loads(record[4])
                    if server[0] in idsList:
                        if record[2] == 1 and server[1] == 0 and record[3] == 0:
                            channel = bot.get_channel(record[1])
                            serverRecord = makeRequest('SELECT * FROM servers WHERE Id=%s',(server[0],))
                            await channel.send(f'Server {serverRecord[0][1]} went down !')
                            makeRequest('UPDATE notifications SET Sent=1 WHERE Id=%s',(record[0],))
        except BaseException as e:
            print(e)
    
bot.add_cog(Updater(bot))

bot.run(conf.token)


