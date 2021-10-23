import aiohttp 
import asyncio
import aiomysql
import json 
import arrow
import discord
from enum import Enum
from cogs.utils.helpers import *
import datetime
import cogs.utils.menus
import cogs.utils.classes as c

class ServerStatus(Enum):
    SERVER_WENT_DOWN=0
    SERVER_WENT_UP=1
    SERVER_WAS_DOWN=2
    SERVER_WAS_UP=3

    @classmethod
    def changed(self,status):
        # if something changed
        if (status == ServerStatus.SERVER_WENT_DOWN or status == ServerStatus.SERVER_WENT_UP):
            return True
        # else 
        else:
            return False


class NotificationsPlugin():

    def __init__(self,updater) -> None:
        print('Initing notifications plugin!')
        # if true than the plugin will modify the record
        # for DB so all mutable plugins will be ran one-by-one and not concurrently
        # (cuz I don't want to mess with syncing of all changes)
        self.mutable = True         
        # main updater class 
        self.updater = updater
        # http pool for APIs
        self.httpPool = self.updater.httpSession
        # sql pool 
        self.sqlPool = self.updater.sqlPool
        # get object to get time
        self.time = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)

    # ALTER TABLE `notifications` ADD `GuildId` BIGINT NOT NULL DEFAULT '0' COMMENT 'Discord guild id. ' AFTER `Data`; 
    async def fixRecords(self, notificationRecords):
        print('handling fixes for db')
        #print(notificationRecords)
        # list of coroutines to run concurrently
        coroutines = []
        # for each record
        for record in notificationRecords:
            #print(record)
            # if value is default value
            if (record[6] == 0):
                #print(record[1])
                # get channel from record
                channel = self.updater.bot.get_channel(record[1])
                #print(channel)
                # if channel isn't found
                if (channel == None):
                    print(f'Channel {record[1]} isn`t found')
                    # skip it
                    continue
                # if found get guild id for this channel
                guildId = channel.guild.id
                # make and append update coroutine
                coroutines.append(self.updater.makeAsyncRequest('UPDATE notifications SET GuildId=%s WHERE Id=%s',(guildId,record[0],)))
        #print(coroutines)
        # we made all coroutines
        # if there any
        if (coroutines.__len__() > 0):
            # run them concurrently
            await asyncio.gather(*coroutines)

    # will be ran by main updater just like regular __init__
    async def init(self):
        print('entered async init')

    # called on each iteration of main loop
    async def loopStart(self):
        # cache all notifications
        self.notificationsCache = await self.updater.makeAsyncRequest('SELECT * FROM notifications')


    async def loopEnd(self):
        pass

    async def serverStatus(self,updateResult):
        # if update failed
        if (updateResult.serverObj == None):
            # if last time server was online
            if (updateResult.serverRecord[6] == 1):
                # server went down
                return ServerStatus.SERVER_WENT_DOWN
            # last time it already was down
            else:
                # server was already down
                return ServerStatus.SERVER_WAS_DOWN
        # update was successful
        else:
            # last time server was down
            if (updateResult.serverRecord[6] == 0):
                # so server went up
                return ServerStatus.SERVER_WENT_UP
            # server was online
            else:
                return ServerStatus.SERVER_WAS_UP
            

    async def makeEmbed(self,status,updateResult,notificationRecord):
        if (status == ServerStatus.SERVER_WENT_DOWN):
            embed = discord.Embed(title=f"Server {await stripVersion(updateResult.cachedServer)} went down!",
            timestamp=self.time.utcnow(), color=discord.Colour.red())   
        else:
         
            embed = discord.Embed(title=f"Server {await stripVersion(updateResult.cachedServer)} went up!",
            timestamp=self.time.utcnow(), color=discord.Colour.green())
        return embed

    async def sendNotifications(self,updateResult,notificationRecords):
        # get status of the server (went or was down/up)
        status = await self.serverStatus(updateResult)
        #print(updateResult.serverRecord)
        #print(notificationRecords)
        #print(f'Server {updateResult.Id}. Status: {status}')
        #print(status.changed(status))
        # if something changed
        if (status.changed(status)):
            # for each notification in DB
            for i in notificationRecords:
                # try to get channel to send notification to
                channel = self.updater.bot.get_channel(i[1])
                # if channel is not found
                if (channel == None):
                    print(f'Channel {i[1]} isn`t found!')
                    # delete the record (in background)
                    asyncio.create_task(self.updater.makeAsyncRequest('DELETE FROM notifications WHERE Id=%s',(i[0],)))
                    # continue with other records
                    continue
                else:
                    try:
                        # send the notification
                        await channel.send(embed = await self.makeEmbed(status,updateResult,i))
                    except discord.errors.Forbidden:
                        # I will implement delete logic later
                        # for now skipp this record
                        continue
                    # change the status in DB to sent in background
                    asyncio.create_task(self.updater.makeAsyncRequest('UPDATE notifications SET Sent=1 WHERE Id=%s',(i[0],)))
                    print(f'Sent notification for {channel.id}')
        # nothing changed
        else:
            return                  

    async def searchForNotificationRecord(self,serverId):
        return [i for i in self.notificationsCache if serverId in json.loads(i[4])] 

    async def handle(self,updateResults):
        print(f'Handling notifications for {[res.Id for res in updateResults]}')
        await self.fixRecords(self.notificationsCache)
        for i in updateResults:
            # search for every notification record
            # for current server
            notifRecords = await self.searchForNotificationRecord(i.Id)
            # if no records found
            if (notifRecords.__len__() <= 0):
                # continue
                continue
            # send notifications
            # we are already in background so it is ok to do
            await self.sendNotifications(i,notifRecords)
        return updateResults