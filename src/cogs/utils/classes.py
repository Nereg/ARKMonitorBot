import asyncio
from json import decoder
import a2s
import arrow
import json
import jsonpickle
import requests
import os
from os import path
import aiohttp
import concurrent.futures._base as base
import socket
import discord
import time

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

    def fromJSON(JSONText, **kwargs):
        decoded = jsonpickle.decode(JSONText, **kwargs) # let's try to decode 
        # we caught a bug 
        # in short after rework "path" to every class changed
        # so we will fix json and decode it 
        if (type(decoded) == type({})):
            # new "root" for classes.py file
            newRoot = 'cogs.utils.'
            # decoded is decoded JSON data
            # we can change it
            # get old path
            # e.g. с.ARKServer
            classPath = decoded['py/object']
            # strip c from path
            #classPath = classPath[1:]
            # prepend new root to old class path
            classPath = newRoot + classPath
            # edit path in old JSON
            decoded['py/object'] = classPath
            # dump JSON text
            text = json.dumps(decoded)
            # and decode one more time
            newDecoded = jsonpickle.decode(text, **kwargs)
            # if new decoded is with error 
            if (type(newDecoded) == type({})):
                print(newDecoded)
                print(type(newDecoded))
                # raise exeption
                raise BaseException()
            # else
            else:
                # return fixed class
                return newDecoded
        else:
            return decoded

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
    

    async def AGetInfo(self):
        """
        Gets info about ARK server
        
        Parameters:
        none (get's all needed info from self)
        Returns:
        self (with updated data)
        """
        try:
            #start = time.perf_counter()
            server = await a2s.ainfo((self.address,self.port)) # get server data
            data = await a2s.arules((self.address,self.port)) # custom ARK data
            #end = time.perf_counter()
            #print(f'Raw async get time: {end - start:.4}')
        except base.TimeoutError as e: 
            raise ARKServerError('1: Timeout',e)
        except socket.gaierror as e:
            raise ARKServerError('2: DNS resolution error',e)
        except ConnectionRefusedError as e:
            raise ARKServerError('3: Connection was refused',e)
        except OSError as e: # https://github.com/Yepoleb/python-a2s/issues/23
            raise ARKServerError('4: OSError',e)
        except a2s.BrokenMessageError as e:
            raise ARKServerError('5: Broken message', e)
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
            raise ARKServerError('6: Not an ARK Server!',e) # it is not an ARK server !
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
        self.ping = int(server.ping * 1000) # ping to the server in ms 
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