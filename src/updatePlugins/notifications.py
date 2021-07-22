import aiohttp 
import asyncio
import aiomysql
import json 
import arrow 
class NotificationsPlugin():

    def __init__(self,updater) -> None:
        print('Initing notifications plugin!')
        # if true than the plugin will modify the record
        # for DB so all mutable plugins will be ran one-by-one and not concurrently
        # (cuz I don't want to mess with syncing of all changes)
        self.mutable = False         
        # main updater class 
        self.updater = updater
        # http pool for APIs
        self.httpPool = self.updater.httpSession
        # sql pool 
        self.sqlPool = self.updater.sqlPool

    # will be ran by main updater just like regular __init__
    async def init(self):
        pass

    # called on each iteration of main loop
    async def loopStart(self):
        # cache all notifications
        self.notificationsCache = await self.updater.makeAsyncRequest('SELECT * FROM notifications')

    async def loopEnd(self):
        pass