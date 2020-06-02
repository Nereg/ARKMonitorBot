from discord.ext import menus
from helpers import * # all our helpers
import classes as c
class SelectServerMenu(menus.Menu):

    async def button_action(self, payload):
        debug = Debuger('buttons')
        debug.debug(payload)
        selected_number = int(payload.emoji.__str__()[:1])
        debug.debug(self.servers)
        self.stop()
        self.result = self.servers[selected_number]
        
    async def addButtonhandler(self,payload):
        debug = Debuger('AddButtonHandler')
        await self.message.edit(content="Enter IP and port like that: `1.1.1.1:1234`")
        debug.debug('Entered ADD button handler!')
        @self.bot.on_message
        async def on_message(message):
            debug.debug('Entered on message handler!')
            if message.author != self.user:
                debug.debug()
                result = await AddServer(message.content,self.ctx)
                self.bot.remove_listener(on_message)
                debug.debug(result)
                return result

                    
    def create_button(self, number): # create button with some number emoji
        button = menus.Button(f'{number}\u20e3', self.__class__.button_action) 
        self.add_button(button)
    
    async def stop_bot(self,test):
        self.result = ''
        self.stop()

    def makeButtons(self): # called in init because needed ) 
        data = makeRequest('SELECT * FROM Servers') # select all servers from DB
        count = data.__len__() # how much we have ?
        for i in range(1,count+1): # for each of them 
            self.create_button(i) # we create button with number TODO : if more than 10 of server added we need pages  
        button = menus.Button('\u274E', self.__class__.stop_bot) # create stop button after ALL buttons will be placed
        self.add_button(button) # and add it
        button = menus.Button('\u2795', self.__class__.addButtonhandler) # create add button to easly add servers
        self.add_button(button) # and add it

    def __init__(self,bot): #init of this class
        super().__init__(timeout=30.0, delete_message_after=True) # set settings 
        self.bot = bot
        self.makeButtons() # see function
        self.servers = [''] # 0 element won't be used 

    async def send_initial_message(self, ctx, channel):
        servers = '' # string with list of servers
        data = makeRequest('SELECT * FROM Servers') # select all servers from DB
        i = 1 # i (yeah classic)
        for result in data: # fro each record in DB
            server = c.ARKServer.fromJSON(result[1]) # construct our class
            self.servers.append(server) # append our server class in right order to use later
            online = bool(1) # exstarct last online state 
            emoji = ':green_circle:' if online else ':red_circle:' # if last online is tru green circle else (if offline) red
            servers += f'{i}. {server.name}  {emoji}  ||{server.ip}|| \n' # construct line and add it to all strings
            i += 1 
        self.ctx = ctx
        return await channel.send(f'Выбери сервер: \n {servers}')
    
    async def prompt(self, ctx): #Entrypoint
        await self.start(ctx, wait=True) # start menu
        return self.result # return result