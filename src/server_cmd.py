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
        self.cfg = config.Config()
        self.bot = bot

    async def serverInfo(self,server,playersList,online,ctx):
        time = datetime.datetime(2000,1,1,0,0,0,0)
        playersList = playersList.list # get list of players
        aliases = await getAlias(0,self.ctx.guild.id,server.ip)
        name = server.name if aliases == '' else aliases
        battleUrl = getattr(server,'battleURL','')
        playersValue = '' # value for players field
        timeValue = '' # value for time field 
        color = randomColor() # pick random color
        for player in playersList: # for each player in player list
            playersValue += player.name + '\n' # add it's name to value
            timeValue += player.time + '\n' # and how much time it played
        if (not online or server.online == 0):
            playersValue = 'No one is on the server'
            timeValue = '\u200B'
        status = ':green_circle:' if online else ':red_circle:' # 
        emb1 = discord.Embed(title=name+' '+status,url=battleUrl,color=color) # first embed
        emb1.add_field(name='Name',value=playersValue)
        emb1.add_field(name='Time played',value=timeValue)
        server.online = server.online if online else 0 # if server offline override online players count
        emb2 = discord.Embed(color=color,timestamp=time.utcnow()) # second embed
        emb2.set_footer(text=f'Requested by {ctx.author.name} • Bot {self.cfg.version} • GPLv3 ',icon_url=ctx.author.avatar_url)
        emb2.add_field(name='IP:',value=server.ip)
        emb2.add_field(name='Players:',value=f'{server.online}/{server.maxPlayers}')
        emb2.add_field(name='Map:',value=server.map)
        emb2.add_field(name='Ping:',value=f'{server.ping} ms.')
        await ctx.send(embed=emb1)
        await ctx.send(embed=emb2)

    # /server command module
    async def oldserverInfo(self,server,playersList,online): # return info about server
        playersList = playersList.list # get list of players
        i = 1 
        players = '' # list of players
        for player in playersList: # for each player in list
            players += '{}. {} {}\n'.format(i,player.name,player.time) # construct string
            i += 1 
        players = 'No one is on the server' if playersList.__len__() <= 0 else players # if no players override our players list
        emoji = ':green_circle:' if online else ':red_circle:' # if server online green circle else red
        server.online = server.online if online else 0 # if server offline override online players count
        aliases = await getAlias(0,self.ctx.guild.id,server.ip)
        print(aliases)
        name = server.name if aliases == '' else aliases
        name = f' {name} {emoji} '.center(50,'=') # construct first line
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
        if (message.__len__() >= 1999):
            message = f'Hello! ARK is so bugged and it returned player list that is bigger than 2k characters which is limit of discord. Pls report this to my support guild. Also there was {i} player on the list.'
        return message # and return it 
    
    @commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True)
    @commands.command()
    @commands.cooldown(10, 60, type=commands.BucketType.user)
    async def server(self,ctx, *args): # /server command handler
        self.ctx = ctx
        debug = Debuger('Server_command') # create debugger
        lang = c.Translation() # load translation
        #debug.debug(args) # debug
        if (args.__len__() <= 0):
            await ctx.send('No mode selected!')
            return 
        mode = args[0]
        if(mode == 'add'): # if /server add 
            debug.debug('Entered ADD mode!') # debug
            if (args.__len__() <= 1): # if no additional args 
                await ctx.send('No IP!') # send error
                return # return
            ip = args[1] 
            servers = await makeAsyncRequest('SELECT * FROM servers WHERE Ip=%s',(ip,)) # get any server with such Ip
            if (servers.__len__() > 0): # if we have it in DB
                Id = servers[0][0] # get it's id in DB
            else:
                Id = await AddServer(ip,ctx) # pass it to function
                if Id == None or Id == 'null': # if server is not added 
                    return # return
            # add if already added check 
            settings = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=%s',(ctx.guild.id,)) # get all servers added to this guild 
            if (settings.__len__() > 0 and settings[0][3] != None): # if we have some results and column isn't empty
                if (Id in json.loads(settings[0][3])): # load ids and check if server is already added
                    await ctx.send('You already added that server!') # return error
                    return 
            data = makeRequest('SELECT * FROM settings WHERE GuildId=%s AND Type=0',(ctx.guild.id,)) # get settings of the guild
            if data.__len__() <= 0: # if we have no settings for that guild
                await makeAsyncRequest('INSERT INTO settings(GuildId, ServersId, Type) VALUES (%s,%s,0)',(ctx.guild.id,json.dumps([Id]),)) # create it 
                await ctx.send('Done!')
            else: # else
                if (data[0][3] == None or data[0][3] == 'null'): # if no servers are added
                    ids = []  # empty array
                else:
                    ids = json.loads(data[0][3]) # else load ids
                ids.append(Id) # append current server id to the list
                await makeAsyncRequest('UPDATE settings SET ServersId=%s WHERE GuildId=%s AND Type=0',(json.dumps(ids),ctx.guild.id,)) # update settings for guild 
                await ctx.send('Done!') # done

        elif (mode == 'info'): # if /server info 
            #debug.debug('Entered INFO mode!') # debug
            selector = Selector(ctx,self.bot,lang) # create server selector
            server = await selector.select() # let the user select server
            if server == '': # if user didn't  selected server
                return # return
            ip = server.ip # else get ip
            servers = await makeAsyncRequest('SELECT * FROM servers WHERE Ip=%s',(ip,))
            server = servers[0]
            print(server[6])
            await self.serverInfo(c.ARKServer.fromJSON(server[4]),c.PlayersList.fromJSON(server[5]),bool(server[6]),ctx)
        elif (mode == 'delete'): # add !exec "delete from notifications where ServersIds like '%4%'"
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
        elif (mode == 'alias'): # if we need to add or delete alias 
            if ('delete' in args): # delete alias 
                guildId = ctx.guild.id # make Id of discord guild
                guildSettings = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=%s',(guildId,)) # get settings for that guild             
                if (guildSettings[0][6] == None or guildSettings[0][6] == ''): # if guild have no prefixes
                    await ctx.send('You have no aliases!') # return
                    return
                selector = Selector(ctx,self.bot,lang) # else 
                serverIp = await selector.select() # let the user select server
                if serverIp == '': # if doesn't selected
                    return # return
                server = await makeAsyncRequest('SELECT * FROM servers WHERE Ip=%s',(serverIp.ip,)) # find needed server
                aliases = json.loads(guildSettings[0][6]) # loads aliases 
                if (server[0][0] in aliases): # if server id is in aliases
                    mainIndex = aliases.index(server[0][0]) # get index of server
                    aliases.pop(mainIndex) # delete (pop) index of the server
                    aliases.pop(mainIndex) # after we poped id alias is in the same position as id so pop twice
                    newAliases = json.dumps(aliases) # dump result  
                    await makeAsyncRequest('UPDATE settings SET Aliases=%s WHERE GuildId=%s',(newAliases,guildId,)) # update DB
                    await ctx.send('Done!') # return
                    return
                else: # if server is not found
                    await ctx.send('You don`t have alias for this server!') # return
                    return
            if (args.__len__() <= 1): # if no additional args 
                guildId = ctx.guild.id # get guild id
                guildSettings = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=%s',(guildId,)) # get settings of that guild
                if (guildSettings[0][6] == None or guildSettings[0][6] == ''): # if we have no aliases
                    await ctx.send('You have no aliases!') # return
                    return
                else: # else
                    aliases = json.loads(guildSettings[0][6]) # load them
                    message = 'List of aliases:\n' # header of message
                    listIndex = 1
                    for i in aliases: # for each of items
                        if(type(i) == type('')): # if item isn't string (it is alias)
                            continue # continue 
                        else: # else (it is server id)
                            server = await makeAsyncRequest('SELECT ServerObj FROM servers WHERE Id=%s',(i,)) # get server object from DB
                            if (server.__len__() <=0): # if we don't have such server 
                                continue # continue 
                            baseIndex = aliases.index(i) # search for id in list
                            serverObj = c.ARKServer.fromJSON(server[0][0]) # decode server object
                            name = await stripVersion(serverObj) # strip version of the server
                            message += f'{listIndex}. {name} ({serverObj.map}) : {aliases[baseIndex+1]}\n' # add line to the message 
                            listIndex +=1 # increase index (yeah i)
                    if (message.__len__()>=2000): # if too much servers
                        raise Exception('Message is over 2K!') # raise
                    await ctx.send(message) # send message
                #await ctx.send('No alias!') # send error
                return # return
            # if we don't have delete and have more then one argument
            selector = Selector(ctx,self.bot,lang) # let the user select server
            serverIp = await selector.select() 
            if serverIp == '':
                return

            alias = discord.utils.escape_mentions(args[1]) #escape alias
            server = await makeAsyncRequest('SELECT * FROM servers WHERE Ip=%s',(serverIp.ip,)) # find needed server
            guildId = ctx.guild.id # make Id of discord guild
            guildSettings = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=%s',(guildId,)) # find guild in settings table (can't be unset because you must add server to select it)
            if (guildSettings[0][6] == None or guildSettings[0][6] == ''): # if it is first server to add alias to
                newAliases = [server[0][0],alias] # make list
                newAliases = json.dumps(newAliases) # jump it into json
            else: # else
                oldAliases = json.loads(guildSettings[0][6]) # load prefixes
                if (server[0][0] in oldAliases): # if we already have an alias for that server 
                    await ctx.send(f'You already have alias `{oldAliases[oldAliases.index(server[0][0])+1]}` for this server!') # return
                    return # else
                oldAliases.append(server[0][0]) # append server id
                oldAliases.append(alias) # and prefix to the list 
                newAliases = json.dumps(oldAliases) # dump the list
            await makeAsyncRequest("UPDATE settings SET Aliases=%s WHERE GuildId=%s",(newAliases,guildId)) # update record in DB 
            await ctx.send('Done!')

            
            
        else:
            await ctx.send('Wrong mode selected !')
            return

    @commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True)
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
        HEADERS = {
    'User-Agent' : "Magic Browser"
        }
        async with aiohttp.request("GET", f'http://api.steampowered.com/ISteamApps/GetServersAtAddress/v0001?addr={splitted[0]}', headers=HEADERS) as resp:
            text = await resp.text()
            text = json.loads(text)
            message = '''
List of detected servers on that ip by steam:

'''
            if (bool(text['response']['success']) or text['response']['servers'].__len__() <= 0):
                i = 1
                for server in text['response']['servers']:
                    ip = server['addr']
                    try:
                        serverClass = await c.ARKServer(ip).AGetInfo()
                        message += f'{i}. {ip} - {serverClass.name} (Online) \n'
                    except:
                        message += f'{i}. {ip} - ??? (Offline) \n'
                    i += 1
            else:
                await ctx.send('No games found on that IP by steam.')
                return
            message += 'Use those ip to add server to bot!'
            if (message.__len_() >= 2000):
                await ctx.send(message[:1999])
                await ctx.send(message[2000:2999]) # would be replaced with functions from helpers.py

