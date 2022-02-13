import discord
from .helpers import *  # all our helpers
from . import classes as c
import asyncio
import json
import datetime

# list of custom ids and labels for them
DEFAULT_BUTTONS = {
    "{}_{}_start": "⏮️",
    "{}_{}_left": "\u2B05",
    "{}_{}_done": "\u2705",
    "{}_{}_right": "\u27A1",
    "{}_{}_end": "⏭️",
    "{}_{}_stop": "\u23F9",
}

# custom button class
class ButtonHandler(discord.ui.Button):
    # I need to specify which properties I need
    __slots__ = "view", "labels", "maxIndex"

    def __init__(self, view, **kwargs) -> None:
        # because we need view
        self.view = view
        # get max index of servers array
        self.maxIndex = view.selector.servers.__len__() - 1
        # get labels of all buttons
        self.labels = list(view.ids.values())
        # create buttons
        super().__init__(**kwargs)

    # call to update message with current server
    async def updateMessage(self):
        # set flag that user selected something
        self.view.selected = True
        # create embed
        embed = await self.view.selector.createEmbed(
            self.view.selector.servers, self.view.result
        )
        # await sendToMe("embed: " + str(embed.fields), self.view.selector.bot)
        # await sendToMe("index: " + str(self.view.result), self.view.selector.bot)
        # edit message
        await self.view.selector.message.edit(embed=embed)

    # this will be called on every button press
    async def callback(self, interaction):
        # await sendToMe('Passed callback checks' + str(self.labels),self.view.selector.bot)
        # await sendToMe("index: "+ str(self.view.result),self.view.selector.bot)
        # await sendToMe("Raw data: "+ str(interaction.data),self.view.selector.bot)
        # await sendToMe("Label: "+ str(self.emoji),self.view.selector.bot)

        # compare current label with all labels
        # go to the start of list
        if str(self.emoji) == self.labels[0]:
            # if we are not at the start of the list
            if self.view.result != 0:
                # go to the start of the list
                self.view.result = 0
                # update message
                await self.updateMessage()
        # go to the previous server
        if str(self.emoji) == self.labels[1]:
            # if we are not at the start if the list
            if self.view.result != 0:
                # go to the previous server
                self.view.result -= 1
                # update message
                await self.updateMessage()
        # we need to select server
        if str(self.emoji) == self.labels[2]:
            self.view.selected = True
            # stop view and do cleanup
            await self.view.clear()
        # if we need to go to next server
        if str(self.emoji) == self.labels[3]:
            # if we are not at the end of the list
            if self.view.result != self.maxIndex:
                # got to the next server
                self.view.result += 1
                # update message
                await self.updateMessage()
        # if we need to go to the last server
        if str(self.emoji) == self.labels[4]:
            # if we are not at the end of the list
            if self.view.result != self.maxIndex:
                # go to the end of the list
                self.view.result = self.maxIndex
                # update message
                await self.updateMessage()
        # if we need to stop
        if str(self.emoji) == self.labels[5]:
            # user canceled selection
            self.view.selected = False
            # stop and clean up view
            await self.view.clear()
        # defer interaction
        await interaction.response.defer()


# view for new selector
class Buttons(discord.ui.View):
    def __init__(self, ids, selector, author_id) -> None:
        # formatted custom ids
        self.ids = ids
        # the callin class itself
        self.selector = selector
        # result will be here
        self.result = 0
        # true if user selected something
        self.selected = False
        # view will only react to this user
        self.author = author_id
        # init view
        super().__init__(timeout=100)
        # for each id + label pair
        for id, label in ids.items():
            # create custom button class
            button = ButtonHandler(
                self, style=discord.ButtonStyle.primary, custom_id=id, emoji=label
            )
            # add that class to view
            self.add_item(button)

    # checks if we are good to process the interaction
    async def interaction_check(self, interaction):
        # get custom id or empty string if there is none
        custom_id = interaction.data.get("custom_id", "")
        # get component type or -1 if there is none
        interaction_type = interaction.data.get("component_type", -1)
        # return true if:
        # custom id is correct
        # interaction type is 2 (button)
        # user interaction is the user which called the command
        return (
            custom_id in self.ids
            and interaction_type == 2
            and interaction.user.id == self.author
        )

    # re raise errors
    async def on_error(self, error, item, interaction):
        raise error

    # clear the view
    async def clear(self):
        # clear items
        self.clear_items()
        # stop the view
        self.stop()

    # on timeout
    async def on_timeout(self):
        # clear the view
        await self.clear()


# class to select a server from DB
class Selector:
    def __init__(self, ctx, bot, lang):
        # context
        self.ctx = ctx
        # if we are using slash commands
        if ctx.interaction is not None:
            # use slash version
            self.select = self.interactionSelect
            # set interaction
            self.interaction = self.ctx.interaction
            # message sent will be here
            self.message = None
        self.bot = bot
        # old translation thing
        # isn't used
        self.l = lang  # classes.Translation
        pass

    # create servers not found embed
    def noServersFoundEmbed(self):
        # create embed
        embed = discord.Embed()
        # paint it red
        embed.color = discord.Colour.red()
        # add info
        embed.add_field(
            name="No servers found!",
            value="You can add servers using `server add` command!",
        )
        # return embed
        return embed

    # create embed for some server from list
    async def createEmbed(self, data, number):
        # construct server object from JSON
        server = c.ARKServer.fromJSON(data[number][4])
        # get online info
        online = bool(data[number][6])
        # get alias
        aliases = await getAlias(0, self.ctx.guild.id, server.ip)
        # set name to alias if any
        name = server.name if aliases == "" else aliases
        # create embed with title and random color
        embed = discord.Embed(title=f"{number+1}. {name}", color=randomColor())
        # set status to green circle if server is online to red if not
        status = (
            ":green_circle: " + self.l.l["online"]
            if online
            else ":red_circle: " + self.l.l["offline"]
        )
        # set yes or no depending on PVE setting
        pve = self.l.l["yes"] if server.PVE else self.l.l["no"]
        # create fields
        embed.add_field(name="IP", value=server.ip)
        embed.add_field(name=self.l.l["status"], value=status)
        embed.add_field(name=self.l.l["version"], value=f"{server.version}")
        embed.add_field(name="PVE?", value=pve)
        embed.add_field(
            name=self.l.l["players_count"], value=f"{server.online}/{server.maxPlayers}"
        )
        embed.add_field(name="Map", value=server.map)
        # return embed
        return embed

    # interaction based server selector
    async def interactionSelect(self):
        # get guild id
        GuildId = self.ctx.guild.id
        # get settings from DB
        data = await makeAsyncRequest(
            "SELECT * FROM settings WHERE GuildId=%s AND Type=0", (GuildId,)
        )
        # if no servers are added
        if data.__len__() == 0:
            # send error message
            await self.ctx.send(embed=self.noServersFoundEmbed())
            return ""  # return
        # if no servers are added
        if data[0][3] == None or data[0][3] == "[]":
            # send error message
            await self.ctx.send(embed=self.noServersFoundEmbed())
            return ""  # return
        # if we have servers added
        Servers = json.loads(data[0][3])  # load them
        # load every server we have
        statement = "SELECT * FROM servers WHERE Id IN ({})".format(
            ", ".join(["{}".format(Servers[i]) for i in range(len(Servers))])
        )
        # try to execute constructed query
        try:
            # execute constructed query
            self.servers = await makeAsyncRequest(statement)
        # if anything happens
        except BaseException as e:
            # send the constructed query to me
            await sendToMe(statement, self.bot, True)
            # re raise error
            raise e
        # construct list of custom id + label pairs
        self.buttonList = {
            # format each key
            key.format(self.ctx.guild.id, self.ctx.author.id): value
            for key, value in DEFAULT_BUTTONS.items()
        }
        # create selector view
        buttons = Buttons(self.buttonList, self, self.ctx.author.id)
        # send first embed with buttons
        self.message = await self.ctx.send(
            embed=await self.createEmbed(self.servers, 0), view=buttons
        )
        # wait until user selected something
        # or the view timed out
        await buttons.wait()
        # delete the message
        await self.message.delete()
        # if user selected something
        if buttons.selected:
            # create server from JSON
            result = c.ARKServer.fromJSON(self.servers[buttons.result][4])
            # return it
            return result
        # if nothing was selected
        else:
            # return empty
            return ""

    # regular server selector
    # maybe the oldest code in this bot
    async def select(self):
        # list of buttons
        reactions = [
            "⏮️",
            "\u2B05",
            "\u2705",
            "\u27A1",
            "⏭️",
            "\u23F9",
        ]
        # get guild id
        GuildId = self.ctx.guild.id
        # get settings from DB
        data = await makeAsyncRequest(
            "SELECT * FROM settings WHERE GuildId=%s AND Type=0", (GuildId,)
        )
        # if no servers are added
        if data.__len__() == 0:
            # send error message
            await self.ctx.send(self.l.l["no_servers_added"].format(self.ctx.prefix))
            return ""  # return
        # if no servers are added
        if data[0][3] == None or data[0][3] == "[]":
            # send error message
            await self.ctx.send(self.l.l["no_servers_added"].format(self.ctx.prefix))
            return ""  # return
        # if we have servers added
        # load them
        Servers = json.loads(data[0][3])
        # create SQL query
        statement = "SELECT * FROM servers WHERE Id IN ({})".format(
            ", ".join(["{}".format(Servers[i]) for i in range(len(Servers))])
        )
        # trying to exec it
        try:
            # execute it
            data = await makeAsyncRequest(statement)
        # if anything bad happens
        except BaseException as e:
            # send the query to me
            await sendToMe(statement, self.bot, True)
            # re raise error
            raise e
        # send first embed
        self.msg = await self.ctx.send(
            self.l.l["server_select"], embed=await self.createEmbed(data, 0)
        )
        # add all reactions
        for reaction in reactions:
            await self.msg.add_reaction(reaction)
        # if 0 while loop is running
        flag = 0
        # the server we are on
        counter = 0
        # true if user selected a server
        selected = False
        # while flag is 0
        while flag == 0:
            try:
                # listen for reaction
                reaction, user = await self.bot.wait_for(
                    "reaction_add",
                    # with timeout of 100
                    timeout=100,
                    # check if it isn't bot's reaction
                    check=lambda r, user: user != self.bot.user
                    # and it is from our message
                    and r.message.id == self.msg.id,
                )
            # if timed out
            except asyncio.TimeoutError:
                # set flag to 1
                flag = 1
                # trying to clear everything
                try:
                    # clear reactions
                    await self.msg.clear_reactions()
                    # leave a note there
                    await self.msg.edit(
                        content="The interactive menu was closed.", embed=None
                    )
                # if the message isn't found
                except discord.errors.NotFound:
                    # return
                    return ""
            # if we have reaction
            else:
                # we need to go to the start og the list
                if str(reaction.emoji) == reactions[0]:
                    # remove reaction
                    await reaction.remove(self.ctx.author)
                    # set counter to 0
                    counter = 0
                    # edit message
                    await self.msg.edit(embed=await self.createEmbed(data, counter))
                # we need to go to the previous server
                if str(reaction.emoji) == reactions[1]:
                    # remove reaction
                    await reaction.remove(self.ctx.author)
                    # if we are not at the end
                    if counter > 0:
                        # go to the previous server
                        counter -= 1
                        # update message
                        await self.msg.edit(embed=await self.createEmbed(data, counter))
                # user selected a server
                elif str(reaction.emoji) == reactions[2]:
                    # delete the message
                    await self.msg.delete()
                    # set selected to true
                    selected = True
                    # set flag to 1
                    flag = 1
                # we need to go to the next server
                elif str(reaction.emoji) == reactions[3]:
                    # remove reaction
                    await reaction.remove(self.ctx.author)
                    # if we are not at the end
                    if counter < data.__len__() - 1:
                        # go to the next server
                        counter += 1
                        # update message
                        await self.msg.edit(embed=await self.createEmbed(data, counter))
                # we need to go to the end of the list
                elif str(reaction.emoji) == reactions[4]:
                    # remove reaction
                    await reaction.remove(self.ctx.author)
                    # go to the end
                    counter = data.__len__() - 1
                    # update message
                    await self.msg.edit(embed=await self.createEmbed(data, counter))
                # we need to stop selector
                elif str(reaction.emoji) == reactions[5]:
                    # delete message
                    await self.msg.delete()
                    # set flag to 1
                    flag = 1
        # if user selected something
        if selected == True:
            # construct server from JSON
            return c.ARKServer.fromJSON(data[counter][4])
        # else
        else:
            # return empty
            return ""
