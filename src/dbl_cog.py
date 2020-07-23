import dbl
import discord
from discord.ext import commands
import config


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.cfg = config.Config()
        self.bot = bot
        self.token = self.cfg.DBLToken # set this to your DBL token
        if (self.token == ''):
            pass
        self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True) # Autopost will post your guild count every 30 minutes