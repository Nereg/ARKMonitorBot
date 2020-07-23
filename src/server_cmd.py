from helpers import *
import classes as c
from menus import *
import discord # main discord libary
from discord.ext import commands # import commands extension
import json
import aiohttp
import classes as c

class ServerCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

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
Status : {'Online' if online else 'Offline'}
Players : {server.online}/{server.maxPlayers}
Map : {server.map}
PVE ? : {server.PVE}
Version : {server.version}
Ping : {server.ping} ms
**Players list**
```
{players}
```
        '''
        return message # and return it 

    @commands.command()
    @commands.cooldown(10, 60, type=commands.BucketType.user)
    async def server(self,ctx, *args): # /server command handler
        debug = Debuger('Server_command') # create debugger
        lang = c.Translation() # load translation
        debug.debug(args) # debug
        mode = args[0]
        if(mode == 'add'): # if /server add 
            debug.debug('Entered ADD mode!') # debug
            if (args == ()): # if no additional args 
                await ctx.send('No IP!') # send error
                return # return
            ip = args[0] # if nwe have ip record it
            servers = makeRequest('SELECT * FROM servers WHERE Ip=%s',(ip,))
            if (servers.__len__() > 0):
                Id = servers[0][0]
            else:
                Id = await AddServer(ip,ctx) # pass it to function
                if Id == None or Id == 'null':
                    return 
            # add if already added check 
            settings = makeRequest('SELECT * FROM settings WHERE GuildId=%s',(ctx.guild.id,))
            if (settings.__len__() > 0 and settings[0][3] != None):
                if (Id in json.loads(settings[0][3])):
                    await ctx.send('You already added that server!')
                    return
            data = makeRequest('SELECT * FROM settings WHERE GuildId=%s AND Type=0',(ctx.guild.id,))
            if data.__len__() <= 0:
                makeRequest('INSERT INTO settings(GuildId, ServersId, Type) VALUES (%s,%s,0)',(ctx.guild.id,json.dumps([Id]),))
                await ctx.send('Done!')
            else:
                if (data[0][3] == None or data[0][3] == 'null'):
                    ids = []  
                else:
                    ids = json.loads(data[0][3])
                ids.append(Id)
                makeRequest('UPDATE settings SET ServersId=%s WHERE GuildId=%s AND Type=0',(json.dumps(ids),ctx.guild.id,))
                await ctx.send('Done!')

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
                print(ip)
                debug.debug(f'Server {ip} is offline!') # also debug
                online = False # set online flag to false
                data = makeRequest('SELECT * FROM servers WHERE Ip = %s',(ip,)) # Select server from DB
                if (data.__len__() > 0): # id we have record with that IP
                    trys = data[0][6] # extract offline trys
                    makeRequest('UPDATE servers SET OfflineTrys=%s, LastOnline=0 WHERE Ip=%s',(trys+1,ip,)) # and update record 
        
            if online: #if server is online
                await ctx.send(self.serverInfo(server,playersList,online)) # send info
                data = makeRequest('SELECT * FROM servers WHERE Ip = %s',(ip,)) # select data from DB
                if (data.__len__() > 0): # if we already have record 
                    makeRequest('UPDATE servers SET ServerObj=%s, PlayersObj=%s,LastOnline=1,OfflineTrys=0  WHERE Ip=%s',(server.toJSON(),playersList.toJSON(),ip)) # update it
                    debug.debug(f'Updated DB record for {ip} server!') # debug
                else: # if we doesn`t have record
                    debug.debug(f'Created DB record for {ip} server!') # debug
                    makeRequest("INSERT INTO servers (ServerObj,PlayersObj,Ip) VALUES (%s,%s,%s)",[server.toJSON(),playersList.toJSON(),server.ip]) # and add record
            else: # id server is offline 
                data = makeRequest('SELECT * FROM servers WHERE Ip = %s',(ip,)) # select data
                if (data.__len__() > 0): # if we have  record about this server
                    await ctx.send(self.serverInfo(c.ARKServer.fromJSON(data[0][4]),c.PlayersList.fromJSON(data[0][5]),online)) # construct classes and send data
                else: # else
                    debug.debug(f'server {ip} is offline and we have no data about it!') # debug
                    await ctx.send('Server is offline and we have no data about it!') # send message
        elif (mode == 'delete'):
            selector = Selector(ctx,self.bot,lang)
            server = await selector.select()
            if server == '':
                return
            if ctx.guild == None : 
                GuildId = ctx.channel.id
                Type = 1
            else:
                GuildId = ctx.guild.id
                Type = 0
            serverId = makeRequest('SELECT * FROM servers WHERE Ip=%s',(server.ip,))
            serverId = serverId[0][0]
            serverIds = makeRequest('SELECT * FROM settings WHERE GuildId=%s AND Type=%s',(GuildId,Type))
            if (serverIds[0][3] == None or serverIds[0][3] == 'null'):
                serverIds = []
            else:
                serverIds = json.loads(serverIds[0][3]) #remove()
            serverIds.remove(serverId)
            makeRequest('UPDATE settings SET ServersId=%s WHERE GuildId=%s AND Type=%s',(json.dumps(serverIds),GuildId,Type))
            await ctx.send('Done!')
        else:
            await ctx.send('Wrong mode selected !')
            return

    @commands.command()
    async def ipfix(self,ctx,*args):
        if (args == ()):
            await ctx.send('No IP!')
            return
        ip = args[0]
        splitted = ip.split(':')
        if (IpCheck(ip) != True): # IP check
            await ctx.send('Something is wrong with **IP**!') # and reply
            return 
        async with self.session as session:
            async with session.get(f'http://api.steampowered.com/ISteamApps/GetServersAtAddress/v0001?addr={splitted[0]}') as resp:
                text = await resp.text()
                text = json.loads(text)
                message = '''
List of detected servers on that ip by steam:

'''
                if (bool(text['response']['success'])):
                    i = 1
                    for server in text['response']['servers']:
                        ip = server['addr']
                        try:
                            serverClass = c.ARKServer(ip).GetInfo()
                            message += f'{i}. {ip} - {serverClass.name} (Online) \n'
                        except:
                            message += f'{i}. {ip} - ??? (Offline) \n'
                        i += 1
                else:
                    await ctx.send('No games found on that IP by steam.')
                    return
                message += 'Use those ip to add server to bot!'
                await ctx.send(message)

