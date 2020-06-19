from helpers import *
import classes as c
from menus import *
import discord # main discord libary
from discord.ext import commands # import commands extension

class ServerCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /server command module
    def serverInfo(self,server,playersList,online): # return info about server
        playersList = playersList.list # get list of players
        i = 1 
        players = '' # list of players
        for player in playersList: # for each player in list
            players += '{}. {} {}\n'.format(i,player.name,player.time) # construct string
            i += 1 
        players = 'Никого нет на сервере' if playersList.__len__() <= 0 else players # if no players override our players list
        emoji = ':green_circle:' if online else ':red_circle:' # if server online green circle else red
        server.online = server.online if online else 0 # if server offline override online players count
        name = f' {server.name} {emoji} '.center(50,'=') # construct first line
        # construct this BIG MAIN MESSAGE
        message = f''' 
**{name}**
IP : {server.ip}
Статус : {'Online' if online else 'Offline'}
Игроков : {server.online}/{server.maxPlayers}
Карта : {server.map}
PVE ? : {server.PVE}
Версия : {server.version}
Ping : {server.ping} ms
**Список игроков**
```
{players}
```
        '''
        return message # and return it 

    @commands.command()
    async def server(self,ctx, mode, *args): # /server command handler
        debug = Debuger('Server_command') # create debugger
        lang = c.Translation()
        debug.debug(args)
        if(mode == 'add'): # if /server add 
            debug.debug('Entered ADD mode!') # debug
            if (args == ()):
                await ctx.send('No IP!')
                return 
            ip = args[0]
            await AddServer(ip,ctx)

        elif (mode == 'info'): # if /server info 
            debug.debug('Entered INFO mode!') # debug
            if (args == ()):
                selector = Selector(ctx,self.bot,lang)
                server = await selector.select()
                if server == '':
                    return
                ip = server.ip
            if (IpCheck(ip) != True): # IP check
                debug.debug(f'Wrong IP : {ip}') # debug
                await ctx.send('Something is wrong with **IP**!') # and reply
                return # if IP is correct
            try: 
                server = c.ARKServer(ip) # construct our classes
                playersList = c.PlayersList(ip)
                playersList.getPlayersList() # and get data
                server.GetInfo()
                online = True # set online flage to true
                debug.debug(f"Server {ip} is up!") # and debug
            except Exception as e: # if any exception
                debug.debug(e) # debug
                debug.debug(f'Server {ip} is offline!') # also debug
                online = False # set online flag to false
                data = makeRequest('SELECT * FROM Servers WHERE IP = ?',[ip]) # Select server from DB
                if (data.__len__() > 0): # id we have record with that IP
                    trys = data[0][4] # extract offline trys
                    makeRequest('UPDATE Servers SET OfflineTrys=?, LastOnline=0 WHERE IP=?',[trys+1,ip]) # and update record 
        
            if online: #if server is online
                await ctx.send(self.serverInfo(server,playersList,online)) # send info
                data = makeRequest('SELECT * FROM Servers WHERE IP = ?',[ip]) # select data from DB
                if (data.__len__() > 0): # if we already have record 
                    makeRequest('UPDATE Servers SET ServerObj=?, DataObj=?,LastOnline=1,OfflineTrys=0  WHERE IP=?',[server.toJSON(),playersList.toJSON(),ip]) # update it
                    debug.debug(f'Updated DB record for {ip} server!') # debug
                else: # if we doesn`t have record
                    debug.debug(f'Created DB record for {ip} server!') # debug
                    makeRequest("INSERT INTO Servers (ServerObj,DataObj,LastOnline,OfflineTrys,IP) VALUES (?,?,?,?,?)",[server.toJSON(),playersList.toJSON(),int(True),0,server.ip]) # and add record
            else: # id server is offline 
                data = makeRequest('SELECT * FROM Servers WHERE IP = ?',[ip]) # select data
                if (data.__len__() > 0): # if we have  record about this server
                    await ctx.send(self.serverInfo(c.ARKServer.fromJSON(data[0][1]),c.PlayersList.fromJSON(data[0][2]),online)) # construct classes and send data
                else: # else
                    debug.debug(f'server {ip} is offline and we have no data about it!') # debug
                    await ctx.send('Server is offline and we have no data about it!') # send message
