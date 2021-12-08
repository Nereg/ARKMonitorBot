import aiohttp
import asyncio
import aiomysql
import json
import arrow
import discord
from enum import Enum
from cogs.utils.helpers import *
import datetime
import cogs.utils.menus as menus
import cogs.utils.classes as c


class NotificationsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        pass

    async def alreadyReceives(self, ctx, serverRecord, discordChannel):
        # if channel is not found set channel name to fallback message
        # else set it to name of the channel
        channelName = f"`{discordChannel.name}`"
        # get server from server record
        server = c.ARKServer.fromJSON(serverRecord[0][4])
        # get prefix for this guild
        prefix = await get_prefix(self.bot, ctx.message)
        # construct error embed
        embed = discord.Embed()
        # set it's title
        embed.title = f"Channel {channelName} already receives notifications!"
        # add some more info
        embed.add_field(
            name=f"Use `{prefix}unwatch` command to no longer receive notifications.",
            value=f"You are receiving notifications for `{await stripVersion(server)}`.",
        )
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
        embed.title = "Success!"
        # add info about notification
        embed.add_field(
            name=f"You are now receiving notification for `{await stripVersion(server)}`",
            value="Have a nice day!",
        )
        # set it's color to green
        embed.color = discord.Colour.green()
        await ctx.send(embed=embed)

    async def noPerms(self, ctx, channel, perms):
        # this will describe which permissions are missing
        missing = ""
        # if both
        if perms.send_messages and perms.embed_links:
            # set it to both
            missing = "send messages and embed links"
        # if only messages
        elif perms.send_messages:
            # set it
            missing = "send messages"
        # if only links
        elif perms.embed_links:
            # set it
            missing = "embed links"
        # default
        else:
            # both
            missing = "send message and embed links"
        # create embed
        embed = discord.Embed()
        # set color
        embed.color = discord.Colour.red()
        # add info
        embed.add_field(
            name="I have insufficient permissions in that channel!",
            value=f"I need `{missing}` in {channel.mention} to send notifications there!",
        )
        # and sent it
        await ctx.send(embed=embed)

    async def canWrite(self, ctx, channel):
        # get our bot memeber in current guild
        botMember = ctx.guild.me
        # get permissions
        perms = channel.permissions_for(botMember)
        # if bot have permission to send messages and embed links
        if perms.send_messages and perms.embed_links:
            # return true
            return True
        else:
            # send error embed
            await self.noPerms(ctx, channel, perms)
            # return false
            return False

    async def deletedServer(self, ctx, serverRecord, channel):
        # get server from server record
        server = c.ARKServer.fromJSON(serverRecord[4])
        # construct error embed
        embed = discord.Embed()
        # add info about notification
        embed.add_field(
            name=f"You unsubscribed from notifications for `{await stripVersion(server)}` !",
            value=f"From now on bot won't send notifications about `{await stripVersion(server)}` in {channel.mention}",
        )
        # set it's color to green
        embed.color = discord.Colour.green()
        await ctx.send(embed=embed)

    async def noNotificationsInChannel(self, ctx, channel):
        # construct error embed
        embed = discord.Embed()
        # add info about notification
        embed.add_field(
            name="You have no notifications for this channel !",
            value=f"You have no notifications for {channel.mention}!",
        )
        # set it's color to green
        embed.color = randomColor()
        await ctx.send(embed=embed)

    async def noNotificationsForThisServer(self, ctx, channel, serverRecord):
        # get server from server record
        server = c.ARKServer.fromJSON(serverRecord[4])
        # construct error embed
        embed = discord.Embed()
        # add info about notification
        embed.add_field(
            name=f"You have no notifications for `{await stripVersion(server)}` in this channel!",
            value=f"You have no notifications for `{await stripVersion(server)}` in {channel.mention}!",
        )
        # set it's color to green
        embed.color = randomColor()
        await ctx.send(embed=embed)

    @commands.bot_has_permissions(
        add_reactions=True,
        read_messages=True,
        send_messages=True,
        manage_messages=True,
        external_emojis=True,
    )
    @commands.command()
    async def watch(self, ctx, discordChannel: discord.TextChannel = None, *argv):
        # if no channel is supplied
        # TODO: add bulk adding of servers
        # if no channel was supplied
        if discordChannel == None:
            # send warning message
            await ctx.send(
                "No optional channel provided. Notifications will be sent to this channel."
            )
            # sent discord channel to current
            discordChannel = ctx.channel

        # check if the bot can write to channel
        if not await self.canWrite(ctx, discordChannel):
            return

        # if no additional args
        if argv.__len__() <= 0:
            # create server selector
            selector = menus.Selector(ctx, self.bot, c.Translation())
            # present server selector
            ip = await selector.select()
            # if nothing was selected
            if ip == "":
                # return
                return
            else:
                # get server record by ip returned by the selector
                server = await makeAsyncRequest(
                    "SELECT * FROM servers WHERE Ip=%s", (ip.ip,)
                )
                # select any record for the discord channel
                notifications = await makeAsyncRequest(
                    "SELECT * FROM notifications WHERE Type=3 AND DiscordChannelId=%s",
                    (discordChannel.id,),
                )
                # if there are some record for it
                if notifications.__len__() > 0:
                    # load list of servers from record
                    serverList = json.loads(notifications[0][4])
                    # if the channel already receives notifications
                    if server[0][0] in serverList:
                        # send error message
                        await self.alreadyReceives(ctx, server, discordChannel)
                    # we need to update record for the channel
                    else:
                        # add id of the new server to list
                        serverList.append(server[0][0])
                        # update record
                        await makeAsyncRequest(
                            "UPDATE notifications SET ServersIds=%s WHERE Id=%s",
                            (
                                json.dumps(serverList),
                                notifications[0][0],
                            ),
                        )
                        # send success message
                        await self.success(ctx, server)
                # we need to create new record for it
                else:
                    # make new list of servers
                    serverList = [server[0][0]]
                    # create new record in the DB
                    await makeAsyncRequest(
                        'INSERT INTO notifications (DiscordChannelId,ServersIds,Type,Sent,Data,GuildId) VALUES (%s,%s,3,0,"{}",%s)',
                        (
                            discordChannel.id,
                            json.dumps(serverList),
                            discordChannel.guild.id,
                        ),
                    )
                    # send success message
                    await self.success(ctx, server)
        else:
            pass

    @commands.bot_has_permissions(
        add_reactions=True,
        read_messages=True,
        send_messages=True,
        manage_messages=True,
        external_emojis=True,
    )
    @commands.command()
    async def unwatch(self, ctx, discordChannel: discord.TextChannel = None):
        if discordChannel == None:
            # send warning message
            await ctx.send(
                "No optional channel provided. Notifications will be deleted from this channel."
            )
            # sent discord channel to current
            discordChannel = ctx.channel
        # select any records for the discord channel
        notifications = await makeAsyncRequest(
            "SELECT * FROM notifications WHERE Type=3 AND DiscordChannelId=%s",
            (discordChannel.id,),
        )
        # if we have no notifications for current channel
        if notifications.__len__() <= 0:
            # send error message
            await self.noNotificationsInChannel(ctx, discordChannel)
            # return
            return
        # create server selector
        selector = menus.Selector(ctx, self.bot, c.Translation())
        # present server selector
        ip = await selector.select()
        # if nothing was selected
        if ip == "":
            # return
            return
        else:
            # get server record by ip returned by the selector
            server = await makeAsyncRequest(
                "SELECT * FROM servers WHERE Ip=%s", (ip.ip,)
            )
            # get server id from server record
            serverId = server[0][0]
            # get ids of servers for this channel
            serversIds = json.loads(notifications[0][4])
            # if we have this server in record
            if serverId in serversIds:
                # remove server id from rest of them
                serversIds.remove(serverId)
                # update the record
                await makeAsyncRequest(
                    "UPDATE notifications SET ServersIds = %s WHERE Id = %s",
                    (
                        json.dumps(serversIds),
                        notifications[0][0],
                    ),
                )
                # and send embed
                await self.deletedServer(ctx, server[0], discordChannel)
            # else
            else:
                # send error message
                await self.noNotificationsForThisServer(ctx, discordChannel, server[0])


def setup(bot: commands.Bot) -> None:
    bot.add_cog(NotificationsCog(bot))
