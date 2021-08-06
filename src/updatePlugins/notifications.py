import aiohttp 
import asyncio
import aiomysql
import json 
import arrow
import discord
from enum import Enum
from helpers import *
import datetime
import menus
import classes as c

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

class NotificationsCog(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        pass

    async def alreadyReceives(self, ctx, serverRecord, notificationRecord):
        # get channel from notification record
        channel = self.bot.get_channel(notificationRecord[1])
        # if channel is not found set channel name to fallback message
        # else set it to name of the channel
        channelName = f'`channel id {notificationRecord[1]}`' if channel else f'`{channel.name}`'
        # get server from server record
        server = c.ARKServer.fromJSON(serverRecord[0][4])
        # get prefix for this guild
        prefix = await get_prefix(self.bot,ctx.message)
        # construct error embed
        embed = discord.Embed()
        # set it's title
        embed.title = f'Channel {channelName} already receives notifications!'
        # add some more info
        embed.add_field(name=f'Use `{prefix}unwatch` command to no longer receive notifications.',
                        value=f'You are receiving notifications for `{await stripVersion(server)}`.')
        # set color of embed 
        embed.color = randomColor()
        # send it 
        await ctx.send(embed=embed)

    async def success(self, ctx, serverRecord):
        # get server from server record
        server = c.ARKServer.fromJSON(serverRecord[0][4])
        # construct error embed
        embed = discord.Embed()
        # set it's title
        embed.title = 'Success!'
        # add info about notification
        embed.add_field(name=f'You are now receiving notification for `{await stripVersion(server)}`',
                        value='Have a nice day!')
        # set it's color to green
        embed.color = discord.Colour.green()
        await ctx.send(embed=embed)

    async def noPerms(self, ctx, channel, perms):
        # this will describe which permissions are missing
        missing = ''
        # if both
        if (perms.send_messages and perms.embed_links):
            # set it to both
            missing = 'send messages and embed links'
        # if only messages
        elif (perms.send_messages):
            # set it
            missing = 'send messages'
        # if only links
        elif (perms.embed_links):
            # set it
            missing = 'embed links'
        # default
        else:
            # both
            missing = 'send message and embed links'
        # create embed
        embed = discord.Embed()
        # set color 
        embed.color = discord.Colour.red()
        # add info
        embed.add_field(name='I have insufficient permissions in that channel!',
                        value=f'I need `{missing}` in {channel.mention} to send notifications there!')
        # and sent it
        await ctx.send(embed=embed)

    async def canWrite(self, ctx, channel):
        # get our bot memeber in current guild
        botMember = ctx.guild.me
        # get permissions 
        perms = channel.permissions_for(botMember)
        print(perms)
        print(perms.send_messages)
        print(perms.embed_links)
        # if bot have permission to send messages and embed links
        if (perms.send_messages and perms.embed_links):
            # return true
            return True
        else:
            # send error embed
            await self.noPerms(ctx, channel, perms)
            # return false
            return False

    @commands.bot_has_permissions(add_reactions=True, read_messages=True, send_messages=True, manage_messages=True, external_emojis=True)
    @commands.command()
    async def watch(self, ctx, discordChannel: discord.TextChannel = None, *argv):
        # if no channel is supplied 
        # TODO: add bulk adding of servers
        # TODO: add custom 'Channel not found' message in error handler
        # if no channel was supplied
        if (discordChannel == None):
            # send warning message
            await ctx.send('No optional channel provided. Notifications will be sent to this channel.')
            # sent discord channel to current
            discordChannel = ctx.channel
        
        # check if the bot can write to channel
        if (not await self.canWrite(ctx, discordChannel)):
            return
        
        # if no additional args
        if(argv.__len__() <= 0):
            # create server selector
            selector = menus.Selector(ctx,self.bot,c.Translation())
            # present server selector
            ip = await selector.select()
            # if nothing was selected
            if (ip == ''):
                # return
                return
            else:
                # get server record by ip returned by the selector
                server = await makeAsyncRequest('SELECT * FROM servers WHERE Ip=%s', (ip.ip,))
                # select any record for the discord channel
                notifications = await makeAsyncRequest('SELECT * FROM notifications WHERE Type=3 AND DiscordChannelId=%s',(discordChannel.id,))
                # if there are some record for it
                if (notifications.__len__() > 0):
                    # load list of servers from record
                    serverList = json.loads(notifications[0][4])
                    # if the channel already receives notifications 
                    if (server[0] in serverList):
                        # send error message
                        await self.alreadyReceives(ctx, server, notifications[0])
                    # we need to update record for the channel
                    else:
                        # add id of the new server to list
                        serverList.append(server[0][0])
                        # update record
                        await makeAsyncRequest('UPDATE notifications SET ServersIds=%s WHERE Id=%s',(json.dumps(serverList),notifications[0][0],))
                        # send success message
                        await self.success(ctx, server)
                # we need to create new record for it
                else:
                    # make new list of servers
                    serverList = [server[0][0]]
                    # create new record in the DB
                    await makeAsyncRequest('INSERT INTO notifications (DiscordChannelId,ServersIds,Type,Sent,Data) VALUES (%s,%s,3,0,"{}")',(discordChannel.id,json.dumps(serverList)))
                    # send success message
                    await self.success(ctx, server)
        else:
            pass

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

    # will be ran by main updater just like regular __init__
    async def init(self):
        pass

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
        print(updateResult.serverRecord)
        print(notificationRecords)
        print(f'Server {updateResult.Id}. Status: {status}')
        print(status.changed(status))
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
                    # send the notification
                    await channel.send(embed = await self.makeEmbed(status,updateResult,i))
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