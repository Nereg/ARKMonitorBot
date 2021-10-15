class Config:
    def __init__(self):
        self.dbHost = 'db'  # host of the DB
        self.dbUser = 'root'  # user to the DB
        self.dbPass = 'secret'  # password to the DB
        self.DB = 'bot'  # DB to use in bot
        self.adminId = ''  # not used right now
        self.token = ''  # token of the bot
        self.defaultPrefix = '!'  # default prefix
        self.DBLToken = ''  # API token for https://top.gg
        self.inviteUrl = 'https://cutt.ly/ARKBot'  # invite URL to use in bot
        self.debug = True  # if output debug messages
        self.client_id = 12131313  # client id of the bot
        self.client_secret = '12131'  # client secret from discord's oauth page
        self.redirect_url = ''  # redirect url to log all users
        self.version = 'DEBUG!'  # version displayed
        self.workersCount = 5  # x update workers per interation
        self.updateFrequency = 120  # 1 update loop in x seconds
        self.backupWebhookUrl = ''  # discord webhook url to use in backup script
        self.logsGuildId = 349178138258833418 # id of a guild where bot will send it's logs
        self.logsChannelId = 874715094645346395 # id of a channel where bot will send it's logs
        self.deprecation = False # set to True to display deprecation warning on every command