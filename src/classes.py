import asyncio
import a2s
import arrow
import json
from helpers import sendToMe
import jsonpickle
import requests
import os
from os import path
import aiohttp
import concurrent.futures._base as base
import socket
import discord

class BattleMetricsAPI():
    def __init__(self):
        #self.limiter = AsyncLimiter(60) # https://aiolimiter.readthedocs.io/en/latest/ 
        pass
    
    @classmethod
    async def getBattlemetricsUrl(self,serverClass):
        '''
        Gets url for given server on battlemetrics.com

        Parameters: 
        serverClass : ARKServer - server to search for

        Returns:
        False ot str : false if url is not found, url if found
        '''
        apiURL = f'https://api.battlemetrics.com/servers?fields[server]=name,ip,portQuery&filter[game]=ark&filter[search]={serverClass.name}' # contruct API url
        async with aiohttp.request("GET", apiURL) as response: # make request 
            if (response.status == 200): # if 200 
                json_data = await response.json() # decode body
                for server in json_data['data']: # for each server
                    serverName = server['attributes']['name'] # extract data
                    serverIp = server['attributes']['ip']
                    serverPort = server['attributes']['portQuery']
                    if (serverClass.name == serverName and serverClass.address == serverIp and serverClass.port == serverPort): # compare to needed server
                        serverId = server['id'] # if match 
                        return f'https://www.battlemetrics.com/servers/ark/{serverId}' # return Battlemetrcis URL
                return False # else return false
            elif (response.status == 429): # if we hit rate limit
                wait = int(response.headers['Retry-After']) # get for how much we must wait
                #print(wait)
                await sendToMe(f'We need to wait for {wait} to get battlemetrics url!')
                await asyncio.sleep(wait) # wait it out
                #print('Failed battlemetrics API call!')
                #print(response.text())
                return await self.getBattlemetricsUrl(serverClass) # remake request 

class ARKServerError(Exception): # ARK server error
    def __init__(self,reason, error, *args, **kwargs) :
        self.reason = reason
        self.error = error
        super().__init__(*args, **kwargs)
    pass

class JSON: #base class
    """Base class for all classes to easly JSON encode and decode"""
    def __init__(self):
        pass

    def toJSON(self):
        return jsonpickle.encode(self) # yeah pickles I know

    def fromJSON(JSONText):
        self = jsonpickle.decode(JSONText) # decode and return
        return self

class ARKServer(JSON):
    """Represents ARK server"""
    def __init__(self,ip):
        """Inititialisation of this class
        ip = ip:port
        """
        self.ip = ip
        self.address , self.port = ip.split(':') # split adress to ip and port
        self.port = int(self.port) # convert port to int
        pass
    

    async def updateOffline(self):
        '''Return a class with all new (e.g not present in current class) properties set to default
        to eliminate difference between updated and not updated servers'''
        if (not hasattr(self, 'battleURL')): # if we don't have battle url already 
            self.battleURL = await BattleMetricsAPI.getBattlemetricsUrl(self) # find it 
        if (not hasattr(self, 'serverSteamId')): # if we don't have server Steam id
            self.serverSteamId = None 
        if (not hasattr(self, 'isARK')): # if we don't know if it is ARK server
            self.isARK = True # let's assume it is ARK server
        return self

    async def AGetInfo(self):
        """
        Gets info about ARK server
        
        Parameters:
        none (get's all needed info from self)
        Returns:
        self (with updated data)
        """
        try:
            server = await a2s.ainfo((self.address,self.port)) # get server data
            data = await a2s.arules((self.address,self.port)) # custom ARK data
        except base.TimeoutError as e: 
            raise ARKServerError('1: Timeout',e)
        except socket.gaierror as e:
            raise ARKServerError('2: DNS resolution error',e)
        except ConnectionRefusedError as e:
            raise ARKServerError('3: Connection was refused',e)
        except OSError as e: # https://github.com/Yepoleb/python-a2s/issues/23
            raise ARKServerError('4: OSError',e)
        self.name = discord.utils.escape_mentions(server.server_name) # get raw name of the server
        version = server.server_name # get name
        first = version.find('(') # split out version
        second = version.rfind(')') # read https://ark.gamepedia.com/Server_Browser#Server_Name    
        if (second == -1 or first == -1): # if version is not found
            self.version = 'No version' # placeholder
            self.stripedName = self.name # fill the gap
        else:            
            self.version = discord.utils.escape_mentions(version[first+1:second]) # extract version
            index = self.name.find(f'- ({version[first+1:second]})') # find end of server name
            self.stripedName = self.name[:index].strip() # put server name without vesrion to the class
        platform = server.platform # get platform server running on
        self.serverSteamId = server.steam_id # get steam id of the server
        if (platform == 'w'): # decode platform server is running on
            platform = 'Windows'
        elif (platform == 'l'):
            platform = 'Linux'
        elif (platform == 'm' or platform == 'o'):
            platform = 'Mac' # =/
        self.platform = platform 
        self.online = server.player_count # get current player count
        self.maxPlayers = server.max_players # get max players server can accept
        self.map = discord.utils.escape_mentions(server.map_name) # get name of server's map
        self.password = server.password_protected # get if server is protected by password
        try:
            self.PVE = bool(int(data['SESSIONISPVE_i'])) # get if server is PVE
        except KeyError as e:
            raise ARKServerError('Not an ARK Server!',e) # it is not an ARK server !
        try:
            self.clusterName = discord.utils.escape_mentions(data['ClusterId_s']) # cluster name
        except KeyError:
            self.clusterName = None # it can be 
        # list of mods installed on the server (but currently it is limited to only first 4 of them)
        self.mods = [] # list of mods
        # example :
        # 'MOD0_s': '2263656440:B21AEF7F4B2485EFA15394881AFB84BC',
        # 'MOD1_s': '1984129536:580AC4F84A4873E0A54447B0CCF11567', 
        # 'MOD2_s': '2250262711:0FCA88A24D63B7B55CF9FBB48A0F1C4A', 
        # 'MOD3_s': '2047318996:27A6E5F84484EE106FBD79A8B09D6794'
        # (part after : is mystery to me )
        if ('MOD0_s' in data): # if we have any mods on server
            self.mods.append(data['MOD0_s'].split(':')[0]) # split the value 
            end = True # it is reverse meaning 
            i = 1 
            while (end): # while not end
    	        if (f'MOD{i}_s' in data): # if we have i-th mod in data
    		        self.mods.append(data[f'MOD{i}_s'].split(':')[0]) # append it's id to the list
    		        i += 1 # increase i
    	        else:
    		        end = False # else end the loop
        #protection against non-ARK servers
        self.isARK = False
        self.game_id = server.game_id # just for fun
        if (server.game == 'ARK: Survival Evolved'):
            self.isARK = True
        if (server.game_id == 346110 or server.game_id == 407530): # ARK:SE and ARK:SOTF
            self.isARK = True
        if (not hasattr(self, 'battleURL')): # if we don't have battle url already 
            battleURL = await BattleMetricsAPI.getBattlemetricsUrl(self) # find it 
            if (battleURL): # if we have url 
                self.battleURL = battleURL
        else:
            if ('coroutine' in self.battleURL): # see line 49 to find why not awaited corutine was passed to the DB
                self.battleURL = await BattleMetricsAPI.getBattlemetricsUrl(self)
        #if (hasattr(self, 'battleURL')): # if we don't have battle url already 
        #    if (self.battleURL == ''):
        #        delattr(self,'battleURL') 
        #self.BattleEye = bool(data['SERVERUSESBATTLEYE_b']) # Is BattleEye used ?
        #self.itemDownload = bool(data['ALLOWDOWNLOADITEMS_i'])  # can you download items to this ARK ?
        #self.characterDownload = bool(data['ALLOWDOWNLOADCHARS_i']) # Can you download characters to this ARK ?
        #self.hours = data['DayTime_s'][:2] # current in-game time
        #self.minutes = data['DayTime_s'][2:]
        self.ping = int(server.ping * 1000) # ping to the server in ms 
        #HEADERS = {'User-Agent' : "Magic Browser"}
        #async with aiohttp.request("GET", 'http://arkdedicated.com/version', headers=HEADERS) as response:
        #    self.newestVersion = discord.utils.escape_mentions(await response.text()) # just in case ya know
        return self

    def GetInfo(self):
        """Function to get info about server
        (To get players list see Playerslist class)
        """
        server = a2s.info((self.address,self.port)) # get server data
        #players = a2s.players(address) #this is list of players I will implement it in another class
        data = a2s.rules((self.address,self.port)) # custom ARK data
        self.name = discord.utils.escape_mentions(server.server_name) # just extract data 
        version = server.server_name #get name
        first = version.find('(') # split out version
        second = version.rfind(')')
        if (second == -1 or first == -1): # if version is not found
            self.version = 'No version' # placeholder
            self.stripedName = self.name # fill the gap
        else:            
            self.version = discord.utils.escape_mentions(version[first+1:second]) # read https://ark.gamepedia.com/Server_Browser#Server_Name           
            index = self.name.find(f'- ({version[first+1:second]})')
            self.stripedName = self.name[:index].strip() # set stripped name
        platform = server.platform # get platform server running on
        if (platform == 'w'): # decode
            platform = 'Windows'
        elif (platform == 'l'):
            platform = 'Linux'
        elif (platform == 'm' or platform == 'o'):
            platform = 'Mac' # =/
        self.platform = platform
        self.online = server.player_count
        self.maxPlayers = server.max_players
        self.map = discord.utils.escape_mentions(server.map_name)
        self.password = server.password_protected
        self.serverSteamId = server.steam_id # get steam id of the server
        try:
            self.PVE = bool(int(data['SESSIONISPVE_i'])) # in data no so much interesting data so let`s parse into class
        except KeyError:
            raise ARKServerError('Not an ARK Server!')
        try:
            self.clusterName = discord.utils.escape_mentions(data['ClusterId_s']) # cluster name
        except KeyError:
            self.clusterName = None
        #self.BattleEye = bool(data['SERVERUSESBATTLEYE_b']) # Is BattleEye used ?
        #self.itemDownload = bool(data['ALLOWDOWNLOADITEMS_i'])  # can you download items to this ARK ?
        #self.characterDownload = bool(data['ALLOWDOWNLOADCHARS_i']) # Can you download characters to this ARK ?
        #self.hours = data['DayTime_s'][:2] # current in-game time
        #self.minutes = data['DayTime_s'][2:]
        self.ping = int(server.ping * 1000)
        # list of mods installed on the server (but currently it is limited to only first 4 of them)
        self.mods = []
        if ('MOD0_s' in data):
            self.mods.append(data['MOD0_s'].split(':')[0])
            end = True
            i = 1
            while (end):
    	        if (f'MOD{i}_s' in data):
    		        self.mods.append(data[f'MOD{i}_s'].split(':')[0])
    		        i += 1
    	        else:
    		        end = False
        #protection against non-ARK servers
        self.isARK = False
        self.game_id = server.game_id # just for fun
        if (server.game == 'ARK: Survival Evolved'):
            self.isARK = True
        if (server.game_id == 346110 or server.game_id == 407530): # ARK:SE and ARK:SOTF
            self.isARK = True
        #self.headers = {'user-agent': 'my-app/0.0.1'}
        #self.newestVersion = discord.utils.escape_mentions(requests.get('http://arkdedicated.com/version', headers=self.headers).text)
        return self
    
class Player(JSON):
    """Internal Player class
    time - arrow library object
    name - string
    """
    def __init__(self,name,time):
        basetime= arrow.get(0)
        time = arrow.get(int(time)) #convert to int because of decimal digits later 
        time = time - basetime
        self.time = time.__str__()
        self.name = discord.utils.escape_mentions(name)
        pass  

class PlayersList(JSON):
    """Players list class
    self.list - is a list of Player class instaces
    """
    def __init__(self,ip):
        """Init of this class
        ip - ip:port
        """
        self.ip = ip
        self.address , self.port = ip.split(':') # split adress to ip and port
        self.port = int(self.port) # convert port to int
        self.list = []
        pass

    async def AgetPlayersList(self):
        """Gets all needed data"""
        try :
            players = await a2s.aplayers((self.address,self.port)) # get raw data
        except base.TimeoutError as e:
            raise ARKServerError('1: Timeout',e)
        except socket.gaierror as e:
            raise ARKServerError('2: DNS resolution error',e)
        except ConnectionRefusedError as e:
            raise ARKServerError('3: Connection was refused',e)
        except OSError as e: # https://github.com/Yepoleb/python-a2s/issues/23
            raise ARKServerError('4: OSError',e)
        result = [] 
        for player in players: # for each player in data
            name = discord.utils.escape_mentions(player.name)
            if (name == ''):
                #continue # remove all unknown players (to match steam server viewer) TODO: remove them from player count
                name = '(unknown player)' # don't worth it and those are steam bugs not mine why I am requried to fix them ?
            try:
                print(name,file=open(os.devnull,'w'))
            except BaseException:
                name = '(invalid name)'
            result.append(Player(name,player.duration)) # construct player class and append it to our results
        self.list = result 
        return self

    def getPlayersList(self):
        """Gets all needed data"""
        players = a2s.players((self.address,self.port)) # get raw data
        result = [] 
        for player in players: # for each player in data
            name = discord.utils.escape_mentions(player.name)
            if (name == ''):
                name = '(unknown player)'
            try:
                print(name,file=open(os.devnull,'w'))
            except BaseException:
                name = '(invalid name)'
            result.append(Player(name,player.duration)) # construct player class and append it to our results
        self.list = result 
        return self


class Translation(): # not used just a param to some classes/functions
    def load_file(self,lang,name='translations'):
        try:
            script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
            rel_path = "translations/{}.json".format(lang)
            file_object  = open(os.path.join(script_dir, rel_path), "r")
        except FileNotFoundError:
            raise Exception('Tarnslation file `{}` not found in `{}`!'.format(lang,path))
        content = file_object.read()
        file_object.close()
        self.json = content 
        self.l = json.loads(self.json)

    def __init__(self,lang='en'):
        self.lang = lang
        self.load_file(lang)
        pass

    def change_lang(self,lang):
        self.lang = lang
        self.load_file(lang)
        pass