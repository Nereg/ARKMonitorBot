import aiohttp 
import asyncio
import aiomysql

class battlemetrics():

    def __init__(self,updater) -> None:
        self.updater = updater
        self.httpPool = self.updater.httpSession
        self.sqlPool = self.updater.sqlPool
        pass

    async def process(self,results):
        pass