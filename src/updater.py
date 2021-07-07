import classes as c  # our classes
from helpers import *  # our helpers
import config  # config
import discord  # main discord libary
from discord.ext import commands  # import commands extension
from discord.ext import tasks
import json
import traceback
import time
from datetime import datetime
import dbl
import os
import io
import traceback
import socket
import menus as m
import concurrent.futures._base as base
import asyncio
import aiohttp


class UpdateResult(c.JSON):
    def __init__(self, result: bool, serverObj: c.ARKServer, playersObj: c.PlayersList,
                serverRecord, reason: c.ARKServerError = None):
        self.result = result # true - update is successful, false - not successful 
        self.serverObj = serverObj # updated server object (can be None if unsuccessful)
        self.playersObj = playersObj # updated players object (can be None if unsuccessful)
        self.ip = self.serverObj.ip # get ip of that server
        self.reason = reason # reason update failed 
        self.serverRecord = serverRecord # record in DB about that server
        self.cachedServer = c.ARKServer.fromJSON(serverRecord[4]) # make classes out of JSON
        self.cachedPlayers = c.PlayersList.fromJSON(serverRecord[5])
        self.Id = serverRecord[0] # id of the server in DB

    def successful(self):
        return self.result
    
    


class NeoUpdater(commands.Cog):
    def __init__(self, bot) -> None:
        print("entered neo updater init")
        self.bot = bot
        self.cfg = config.Config()
        # count of concurrent functions to run
        self.workersCount = self.cfg.workersCount
        self.handlers = []  # array of handler classes which would handle results
        self.additions = []  # array of additional classes which would update some info
        self.servers = None # local cache of all servers from DB. Updated on every iteration
        self.serversIds = None # list of ids of the servers from local cache for faster searching
        self.update.start() # start main loop 

    def cog_unload(self):  # on unload
        self.update.cancel()  # cancel the task
                              # self.destroy will run anything to destroy 

    # generates array of ids of servers from local cache
    async def flattenCache(self):
        # list comprehension is faster
        return [i[0] for i in self.servers] 

    # searches for an id in local cache (self.servers)
    async def searchCache(self, id: int):
        '''
        Searches for a server record in local cache.
        If found returns the server record if not returns None
        '''
        try:
            # search for that id in flattened local cache 
            position = self.serversIds.index(id)
        # if not found
        except ValueError:
            # return none
            return None
        # return server record from found position
        return self.servers[position]
        
    # performs SQL request using aiomysql pool instead of regular function
    async def makeAsyncRequest(self, SQL, params=()):
        conn = await self.sqlPool.acquire()  # acquire one connecton from the pool
        async with conn.cursor() as cur:  # with cursor as cur
            await cur.execute(SQL, params)  # execute SQL with parameters
            result = await cur.fetchall()  # fetch all results
            await conn.commit()  # commit changes
        self.sqlPool.release(conn)  # release current connection to the pool
        return result  # return result

    # let's do anything normal __init__ can't do 
    async def init(self): 
        self.httpSession = aiohttp.ClientSession()  # for use in http API's
        self.sqlPool = await aiomysql.create_pool(host=self.cfg.dbHost, port=3306,  # somehow works see:
                                                  # https://github.com/aio-libs/aiomysql/issues/574
                                                  user=self.cfg.dbUser, password=self.cfg.dbPass,
                                                  db=self.cfg.DB, loop=asyncio.get_running_loop(), minsize=self.workersCount)
        print("Finished async init")
    
    # function that updates some server
    async def updateServer(self, serverRecord, Id:int):
        Ip = serverRecord[1] # get IP of the server 
        server = c.ARKServer(Ip) # construct classes 
        players = c.PlayersList(Ip)
        updateServer = server.AGetInfo() # make coroutines
        updatePlayers = players.AgetPlayersList()
        
        try:
            # run coroutines concurrently
            results = await asyncio.gather(updateServer, updatePlayers)
        except c.ARKServerError as e: # if fails
            return UpdateResult(False, None, None, serverRecord, e) # return fail and reason
        
        return UpdateResult(True, results[0], results[1], serverRecord) # else return success

    async def performance(self,globalStart,globalStop,localStart,chunkTimes):
        # calculate global time 
        globalTime = globalStop - globalStart
        avgChunk = sum(chunkTimes) / len(chunkTimes) 
        minChunk = min(chunkTimes)
        maxChunk = max(chunkTimes)
        await sendToMe(f"New updater took {globalTime:.4f} sec. to update {self.serversIds.__len__()} servers.", self.bot)
        await sendToMe(f"Min chunk time: {minChunk:.4f}\nAvg chunk time: {avgChunk:.4f}\nMax chunk time: {maxChunk:.4f}",self.bot)

    async def save(self,results):
        tasks = [] # list of tasks to run concurrently
        # for each server on list
        for result in results:
            # if update is successful
            if (result.successful()):
                # make request
                task = self.makeAsyncRequest("UPDATE servers SET LastOnline=1, OfflineTrys=0, ServerObj=%s, PlayersObj=%s WHERE Id=%s",
                (result.serverObj.toJSON(), result.playersObj.toJSON(), result.Id,))
                # append it to list of tasks
                tasks.append(task)
            else:
                # make request
                task = self.makeAsyncRequest("UPDATE servers SET LastOnline=0, OfflineTrys=%s WHERE Id=%s",
                                            (result.serverRecord[7] + 1, result.Id,))
                # append it to list of tasks
                tasks.append(task)
        # after each task generated
        # run them concurrently
        await asyncio.gather(*tasks)

    # main updater loop
    @tasks.loop(seconds=100.0)
    async def update(self):
        await sendToMe("Entered updater loop!",self.bot)
        globalStart = time.perf_counter() # start performance timer
        chunksTime = [] # array to hold time each chunk took to process
        self.servers = await self.makeAsyncRequest("SELECT * FROM servers") # update local cache
        self.serversIds = await self.flattenCache() # make array with ids only     
        serversCount = self.servers.__len__() # get how many servers we need to update

        tasks = [] # list of tasks to run concurrently
        localStart = time.perf_counter() # start performance timer for this chunk
        # for each server
        for i in range(1,serversCount):
            # search for current server
            currentServer = await self.searchCache(i)
            # if server not found
            if (not currentServer):
                # skip this server
                continue
            # make coroutine
            task = self.updateServer(currentServer,i)
            # append new task to task list
            tasks.append(task)
            # if enough tasks generated 
            if (tasks.__len__() >= self.workersCount):
                # run them concurrently
                results = await asyncio.gather(*tasks)
                # empty the list of tasks
                tasks = []
                #########
                # Space for more functions
                #########
                # save results in DB
                await self.save(results)
                # add chunk time to array
                chunksTime.append(time.perf_counter() - localStart)
                # reset timer 
                localStart = time.perf_counter()
        # if there is some tasks left 
        if (tasks.__len__() != 0):
            # run them concurrently
            results = await asyncio.gather(*tasks)
            # empty the list of tasks
            tasks = []
            # save results in DB
            await self.save(results)
        globalStop = time.perf_counter()
        # send performance data to me
        await self.performance(globalStart,globalStop,localStart,chunksTime)

    # will be executed before main loop starts
    @update.before_loop
    async def before_update(self):
        await self.init()
        print("Inited updater loop!")

    # on error handler
    @update.error
    async def onError(self,error):
        errors = traceback.format_exception(
        type(error), error, error.__traceback__)
        errors_str = ''.join(errors)
        await sendToMe(errors_str,self.bot,True)

    # will be executed before main loop will be destroyed
    @update.after_loop
    async def destroy(self):
        self.sqlPool.close()
        await self.httpSession.close()
        print("Destroyed updater loop!")

#def setup(bot):
    #bot.add_cog(Updater(bot))
