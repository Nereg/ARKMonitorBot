import a2s
import arrow
import json
import jsonpickle
import requests
import os
from os import path

class JSON: #base class
    """Base class for all classes to easly JSON encode and decode"""
    def __init__(self):
        pass

    def toJSON(self):
        return jsonpickle.encode(self) # yeah pickles I know

    def fromJSON(JSONText):
        self = jsonpickle.decode(JSONText)
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
    
    def GetInfo(self):
        """Function to get info about server
        (To get players list see Playerslist class)
        """
        server = a2s.info((self.address,self.port)) # get server data
        #players = a2s.players(address) #this is list of players I will implement it in another class
        data = a2s.rules((self.address,self.port)) # custom ARK data

        version = server.server_name #get name
        first = version.find('(') # split out version
        second = version.rfind(')')
        self.version = version[first+1:second] # read https://ark.gamepedia.com/Server_Browser#Server_Name

        platform = server.platform # get platform server running on
        if (platform == 'w'): # decode
            platform = 'Windows'
        elif (platform == 'l'):
            platform = 'Linux'
        elif (platform == 'm' or platform == 'o'):
            platform = 'Mac' # =/
        self.platform = platform

        self.name = server.server_name # just extract data 
        self.online = server.player_count
        self.maxPlayers = server.max_players
        self.map = server.map_name
        self.password = server.password_protected
        self.PVE = bool(int(data['SESSIONISPVE_i'])) # in data no so much interesting data so let`s parse into class
        try:
            self.clusterName = data['ClusterId_s'] # cluster name
        except KeyError:
            self.clusterName = None
        self.BattleEye = bool(data['SERVERUSESBATTLEYE_b']) # Is BattleEye used ?
        self.itemDownload = bool(data['ALLOWDOWNLOADITEMS_i'])  # can you download items to this ARK ?
        self.characterDownload = bool(data['ALLOWDOWNLOADCHARS_i']) # Can you download characters to this ARK ?
        self.hours = data['DayTime_s'][:2] # current in-game time
        self.minutes = data['DayTime_s'][2:]
        self.ping = int(server.ping * 1000)
        headers = {'user-agent': 'my-app/0.0.1'}
        self.newestVersion = requests.get('http://arkdedicated.com/version', headers=headers).text
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
        self.name = name
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

    def getPlayersList(self):
        """Gets all needed data"""
        players = a2s.players((self.address,self.port)) # get raw data
        result = [] 
        for player in players: # for each player in data
            name = player.name
            if (name == ''):
                name = '(unknown player)'
            try:
                print(name,file=open(os.devnull,'w'))
            except BaseException:
                name = '(invalid name)'
            result.append(Player(name,player.duration)) # construct player class and append it to our results
        self.list = result 
        return self

class GuildSettings(JSON):
    """Class for guild settingslike prefix and anything in future"""
    def __init__(self,prefix='!',data={}):
        """Just init"""
        self.prefix=prefix
        self.data=data
        pass

    def addToData(self,key,value,override=False):
        if (key in self.data and override == False):
            raise Exception(f'{key} is in data array and override is false!')
        else:
            self.data[key] = value
            return self.data

class Translation():
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