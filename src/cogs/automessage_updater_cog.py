from cogs.utils.helpers import *
from discord.ext import tasks
import discord
import cogs.utils.menus as m
import datetime
import time
import traceback

class AutoMessageUpdaterCog(commands.Cog):
    def __init__(self, bot) -> None:
        print("Entered auto message updater init")
        self.bot = bot
        self.cfg = config.Config()
        # count of concurrent functions to run
        self.workersCount = self.cfg.workersCount
        self.refresh.start()  # start main loop
        self.updatedMessages = 0
        # list of defective auto messages
        self.defective = {}
        # how often in seconds to reset self.defective
        self.resetTimer = 600
        # threshold before deleting an automessage from db
        self.threshold = 10

    async def makeMessage(self, serverId, guildId, serverIp=""):
        # if we have server ip
        if serverIp != "":
            # select a server by it
            server = await makeAsyncRequest(
                "SELECT * FROM servers WHERE Ip=%s", (serverIp,)
            )
        # else we gave it's id
        else:
            # select a server by id
            server = await makeAsyncRequest(
                "SELECT * FROM servers WHERE Id=%s", (serverId,)
            )
        # create server and players on it from server record
        serverObj = c.ARKServer.fromJSON(server[0][4])
        playersObj = c.PlayersList.fromJSON(server[0][5])
        # get server's alias
        alias = await getAlias(serverId, guildId)
        # if we have alias
        if alias != "":
            # use it
            name = alias
        # else
        else:
            # use server's name
            name = await stripVersion(serverObj)
        # create embed
        embed = discord.Embed(title=name)
        # if there are any players
        if playersObj.list.__len__() > 0:
            # variables
            nameValue = ""
            timevalue = ""
            # for each player in list
            for player in playersObj.list:
                # and it's name and time to variables
                nameValue += f"{player.name}\n"
                timevalue += f"{player.time}\n"
            # TODO: add check for strings larger than Discord limit
            # then add these variables to embed
            embed.add_field(name="Name", value=nameValue, inline=True)
            embed.add_field(name="Time", value=timevalue, inline=True)
        # if there is no players
        else:
            # add this info into embed
            embed.add_field(name="No one is on the server", value="\u200B", inline=True)
        # if server is online set status to online string
        # else set to offline string
        status = (
            ":green_circle: Online" if server[0][6] == 1 else ":red_circle: Offline"
        )
        # add other info about server
        embed.add_field(name="Status", value=status, inline=False)
        embed.add_field(name="Ping", value=f"{serverObj.ping} ms", inline=True)
        embed.add_field(name="Map", value=serverObj.map, inline=True)
        embed.add_field(name="IP", value=f"{serverObj.ip}", inline=True)
        # get current time
        curTime = datetime.datetime.utcnow()
        # set footer
        embed.set_footer(text=f'Updated: {curTime.strftime("%m.%d at %H:%M")} (UTC)')
        # paint in random color
        embed.color = randomColor()
        # return embed
        return embed

    async def resetDefective(self):
        """Simple timer to reset self.defective dictionary"""
        # sleep
        await asyncio.sleep(self.resetTimer)
        # reset dictionary
        self.defective = {}
        # print(f'reset ! {self.resetTimer}')
        # start timer again
        asyncio.create_task(self.resetDefective())

    async def deleteDefective(self):
        '''Deletes all faulty recors from db'''
        # array of record to delete
        toDelete = []
        # for each record in list of defective records
        for id, value in self.defective.items():
            # if it's failed to update more than 
            # self.threshold times
            if (value >= self.threshold):
                # add it's id
                toDelete.append(id)
        # if there are records to delete
        if (toDelete.__len__() > 0):
            # construct query
            query = f'DELETE * FROM automessages WHERE Id IN ({",".join(["%s"] * len(toDelete))})'
            print(query)
            print(toDelete)
            # execute it
            await makeAsyncRequest(query, toDelete)

    async def refreshAutomessage(self, message):
        # get guild from record
            guild = self.bot.get_guild(message[5])
            # if we can't get guild
            if guild == None:
                # if record is found add 1 to number in it
                # else create it with value of 1
                self.defective[message[0]] = self.defective.get(message[0], 0) + 1
                # skip record
                return
            # get channel from record
            channel = guild.get_channel(message[1])
            # if we can't get channel
            if channel == None:
                # print(f"can`t get channel {message[1]}")
                # if record is found add 1 to number in it
                # else create it with value of 1
                self.defective[message[0]] = self.defective.get(message[0], 0) + 1
                # skip record
                return
            # get message from record
            msg = channel.get_partial_message(message[2])
            # if we can't get channel
            if msg == None:
                # print(f"can`t get msg {message[2]}")
                # if record is found add 1 to number in it
                # else create it with value of 1
                self.defective[message[0]] = self.defective.get(message[0], 0) + 1
                # skip record
                return
            # generate embed
            embed = await self.makeMessage(message[3], message[5])
            try:
                # edit message
                await msg.edit(embed=embed)
                self.updatedMessages += 1
            # if we can't edit message
            except discord.Forbidden:
                # if record is found add 1 to number in it
                # else create it with value of 1
                self.defective[message[0]] = self.defective.get(message[0], 0) + 1
                # skip record
                return
            # if we can't find message
            except discord.errors.NotFound:
                # if record is found add 1 to number in it
                # else create it with value of 1
                self.defective[message[0]] = self.defective.get(message[0], 0) + 1
                # skip record
                return
            # if any other error
            except BaseException as e:
                asyncio.create_task(
                    sendToMe(f"Error in auto messages: {e}", self.bot, True)
                )

    async def performance(self, globalStart, globalStop, localStart, chunkTimes):
        #print(chunkTimes)
        # calculate global time
        globalTime = globalStop - globalStart
        avgChunk = sum(chunkTimes) / len(chunkTimes)
        minChunk = min(chunkTimes)
        maxChunk = max(chunkTimes)
        await sendToMe(
            f"Automessages took {globalTime:.4f} sec. to update {self.updatedMessages} messages.",
            self.bot,
        )
        await sendToMe(
            f"Min chunk time: {minChunk:.4f}\nAvg chunk time: {avgChunk:.4f}\nMax chunk time: {maxChunk:.4f}",
            self.bot,
        )

    @tasks.loop(seconds=100.0)
    async def refresh(self):
        globalStart = time.perf_counter()  # start performance timer
        chunksTime = []  # array to hold time each chunk took to process
        # reset counter
        self.updatedMessages = 0
        # get all messages
        messages = await makeAsyncRequest("SELECT * FROM automessages")
        tasks = []
        localStart = time.perf_counter()  # start performance timer for this chunk
        # for each record
        for message in messages:
            # make coroutine
            task = self.refreshAutomessage(message)
            # append new task to task list
            tasks.append(task)
            # if enough tasks generated
            if tasks.__len__() >= self.workersCount:
                # run them concurrently
                await asyncio.gather(*tasks)
                # empty the list of tasks
                tasks = []
                # add chunk time to array
                chunksTime.append(time.perf_counter() - localStart)
                #print(f"Updated {[i.Id for i in results]}")
                # reset timer
                localStart = time.perf_counter()     
                # if there is some tasks left
        if tasks.__len__() != 0:
            # run them concurrently
            await asyncio.gather(*tasks)
            # add chunk time to array
            chunksTime.append(time.perf_counter() - localStart)
            # reset timer
            localStart = time.perf_counter()  
            # empty the list of tasks
            tasks = []
            # here
        # delete any defective records from db
        await self.deleteDefective()
        globalStop = time.perf_counter()
        # send performance data to me
        await self.performance(globalStart, globalStop, localStart, chunksTime)

    @refresh.error
    async def onError(self, error):
        errors = traceback.format_exception(type(error), error, error.__traceback__)
        errors_str = "".join(errors)
        await sendToMe(f"Error in automessages!\n```{errors_str}```", self.bot)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AutoMessageUpdaterCog(bot))
