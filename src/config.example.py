class Config:
    def __init__(self):
        self.dbHost = 'db'
        self.dbUser = 'root'
        self.dbPass = 'secret' #secret
        self.DB = 'bot'
        self.adminId = ''
        self.token = '' # discord token of the bot
        self.defaultPrefix = '!' # default prefix
        self.DBLToken = '' # top.gg API token to submit count of server 
        self.inviteUrl = 'https://cutt.ly/ARKBot' # invite URL
        self.debug = True # more logging output
        self.client_id = 713272720053239808 # client id
        self.client_secret = '12131' # client secret
        self.redirect_url = 'http://ark.fvds.ru/' # redirect URL
        self.version = 'DEBUG!' # version
        self.workersCount = 5 # and workers count (more -> faster updates -> more load)