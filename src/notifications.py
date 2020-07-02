from helpers import * # all our helpers
import classes as c # all our classes
import discord # main discord lib
from discord.ext import commands
import menus as m
import server_cmd as server # import /server command module (see server_cmd.py)
import json
import config

class NotificationComands(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.cfg = config.Config()
        self.t = c.Translation()

    @commands.command
    def watch(self,ctx):
        selector = m.Selector(ctx,self.bot,self.t)
        server = await selector.select()
        if server == '':
            return
        ip = server.ip
        notifications = makeRequest('SELECT * FROM notifications WHERE ')