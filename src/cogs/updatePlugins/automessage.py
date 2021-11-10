from cogs.utils.helpers import *
import discord
import cogs.utils.menus as m
import datetime
import time


class AutoMessagesPlugin:
    def __init__(self, updater) -> None:
        print("Initing auto messages plugin!")
        # if true than the plugin will modify the record
        # for DB so all mutable plugins will be ran one-by-one and not concurrently
        # (cuz I don't want to mess with syncing of all changes)
        self.mutable = False
        # main updater class
        self.updater = updater
        # http pool for APIs
        self.httpPool = self.updater.httpSession
        # shortcut
        self.bot = self.updater.bot
        # get object to get time
        self.time = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        # debug variable to track how many messages we updated
        self.updatedMessages = 0
        # list of defective auto messages
        self.defective = {}
        # how often in seconds to reset self.defective
        self.resetTimer = 600
        # start timer
        asyncio.create_task(self.resetDefective())
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

    # will be ran by main updater just like regular __init__
    async def init(self):
        pass
        # print("entered async init")

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

    async def refresh(self):
        # start performance timer
        start = time.perf_counter()
        # reset counter
        self.updatedMessages = 0
        # get all messages
        messages = await self.updater.makeAsyncRequest("SELECT * FROM automessages")
        # for each record
        for message in messages:
            # get guild from record
            guild = self.bot.get_guild(message[5])
            # if we can't get guild
            if guild == None:
                # if record is found add 1 to number in it
                # else create it with value of 1
                self.defective[message[0]] = self.defective.get(message[0], 0) + 1
                # skip record
                continue
            # get channel from record
            channel = guild.get_channel(message[1])
            # if we can't get channel
            if channel == None:
                # print(f"can`t get channel {message[1]}")
                # if record is found add 1 to number in it
                # else create it with value of 1
                self.defective[message[0]] = self.defective.get(message[0], 0) + 1
                # skip record
                continue
            # get message from record
            msg = channel.get_partial_message(message[2])
            # if we can't get channel
            if msg == None:
                # print(f"can`t get msg {message[2]}")
                # if record is found add 1 to number in it
                # else create it with value of 1
                self.defective[message[0]] = self.defective.get(message[0], 0) + 1
                # skip record
                continue
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
                continue
            # if we can't find message
            except discord.errors.NotFound:
                # if record is found add 1 to number in it
                # else create it with value of 1
                self.defective[message[0]] = self.defective.get(message[0], 0) + 1
                # skip record
                continue
            # if any other error
            except BaseException as e:
                asyncio.create_task(
                    sendToMe(f"Error in auto messages: {e}", self.bot, True)
                )
        # delete any defective records from db
        await self.deleteDefective()
        # end performance timer
        end = time.perf_counter()
        # send stats
        await sendToMe(
            f"Updated {self.updatedMessages}/{messages.__len__()} auto messages!\nIt took: {end - start:.4} sec.\n{self.defective}",
            self.bot,
        )

    # https://quantlane.com/blog/ensure-asyncio-task-exceptions-get-logged/
    def handle_task_result(self, task: asyncio.Task) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            pass  # Task cancellation should not be logged as an error.
        except Exception as e:
            asyncio.create_task(
                sendToMe(f"unhandled {e} in automessage task", self.bot, True)
            )

    # called on each iteration of main loop
    async def loopStart(self):
        # refresh messages in background
        task = asyncio.create_task(self.refresh())
        task.add_done_callback(self.handle_task_result)

    async def loopEnd(self):
        pass
        # await sendToMe(f"Updated {self.updatedMessages} auto messages!", self.bot)

    async def handle(self, updateResults):
        pass
