from helpers import * # all our helpers
import classes as c # all our classes
import discord # main discord lib
from discord.ext import commands
import menus as m
import server_cmd as server # import /server command module (see server_cmd.py)
import json
import config
import datetime

class Automessage(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.cfg = config.Config()
        self.t = c.Translation()
    
    @commands.bot_has_permissions(add_reactions=True,read_messages=True,send_messages=True,manage_messages=True,external_emojis=True)
    @commands.command()
    async def automessage(self, ctx, *agrs):        
        try:
            channel = await discord.ext.commands.TextChannelConverter.convert(ctx,agrs[1])
        except discord.BadArgument:
            await ctx.send('Channel is not found!')
            return
        selector = m.Selector(ctx,self.bot,c.Translation())
        serverIp = await selector.select()
        if serverIp == '':
            return
        print(channel.name)

        
    