class Config:
    def __init__(self):
        self.dbPath = '../main.db' # db path relative to src folder
        self.adminId = '' # discord id of bot admin
        self.token = '' # bot's token
        self.defaultPrefix = '!' # default bot's commands prefix
        self.inviteUrl = 'https://discord.com/oauth2/authorize?client_id=713272720053239808&scope=bot&permissions=8' #fix permisions!