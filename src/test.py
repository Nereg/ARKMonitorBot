from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
import discord
import classes as c # our classes
from helpers import * # our helpers
import config  # config
import discord # main discord libary
from discord.ext import commands # import commands extension

class Notifications(commands.Cog):
    def __init__(self, bot):   
        self.bot = bot
        self.schelduler = AsyncIOScheduler()
        self.schelduler.add_job(self.tick, 'interval', seconds=10)
    
    async def tick(self):
        print('test')