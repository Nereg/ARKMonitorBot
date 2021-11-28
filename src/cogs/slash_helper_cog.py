from cogs.utils.helpers import sendToMe
from discord.ext import commands
import discord
import aiohttp
import asyncio

class SlashCommandsHelper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.appId = bot.cfg.app_id
        self.cfg = bot.cfg
        self.token = self.cfg.token
        self.authheader = {"Authorization": f"Bot {self.token}"}
        self.cogs = self.bot.myCogs

    async def cog_check(self, ctx):
        return (
            await self.bot.is_owner(ctx.author) or ctx.author.id == 277490576159408128
        )

    async def cog_before_invoke(self, ctx):
        # if we have no http pool
        if getattr(self, "httpSession", None) == None:
            # create it
            self.httpSession = aiohttp.ClientSession()

    @commands.Cog.listener()
    # on any interaction
    async def on_interaction(self, interaction):
        await sendToMe(interaction.data, self.bot)
        await sendToMe(interaction.data['type'], self.bot)
        # if this is a slash command
        if (interaction.data['type'] == 1):
            # get it's name
            name = interaction.data['name']
            await sendToMe(name, self.bot)
            # run all handlers (may cause chaos if something matches in two handlers)
            await asyncio.gather(*[i.slashHandler(interaction, name) for i in self.cogs])

    def listCommands(self, commands):
        types = {1: "Slash command", 2: "User command", 3: "Message command"}
        output = ""
        for command in commands:
            output += "=======================\n"
            output += f'Id: {command["id"]}\n'
            output += f'Command type: {types.get(command["type"], "Unknown type")}\n'
            output += f'Guild id: {command.get("guild_id","No guild id")}\n'
            output += f'Command name: {command["name"]}\n'
            output += f'Command description: {command["description"] if command["description"] != "" else "No description"}\n'
        return output

    @commands.command()
    async def listAllCommands(self, ctx, GuildId: int = None):
        # https://discord.com/api/v8/applications/<my_application_id>/commands
        resp = await self.httpSession.get(
            f"https://discord.com/api/v8/applications/{self.appId}/commands",
            headers=self.authheader,
        )
        # https://discord.com/api/v8/applications/{application.id}/guilds/{guild.id}/commands
        commands = await resp.json()
        await ctx.send(commands)
        text = "List of **global** slash commands:\n"
        text += self.listCommands(commands)
        if commands.__len__() <= 0:
            text += "No global commands\n"
        if not GuildId:
            GuildId = ctx.guild.id
        text += f"List of **local** commands for guild `{GuildId}`\n"
        resp = await self.httpSession.get(
            f"https://discord.com/api/v8/applications/{self.appId}/guilds/{GuildId}/commands",
            headers=self.authheader,
        )
        localCommands = await resp.json()
        text += self.listCommands(localCommands)
        text += "List of loaded slash cogs:\n"
        text += str(self.cogs) + '\n'
        text += 'List of slash command handlers:\n'
        text += str(*[i.slashHandler for i in self.cogs]) + '\n'
        await ctx.send(text)
        pass

    @commands.command()
    async def addGuildCommand(
        self, ctx, Name: str, Description: str, Type=1, guildId=None, *, RawJson=None
    ):
        if not guildId:
            guildId = ctx.guild.id
        url = f"https://discord.com/api/v8/applications/{self.appId}/guilds/{guildId}/commands"
        headers = self.authheader
        headers["Content-Type"] = "application/json"
        if not RawJson:
            json = {
                "name": Name,
                "type": Type,
                "description": Description,
                "options": [
                    {
                        "name": "animal",
                        "description": "The type of animal",
                        "type": 3,
                        "required": True,
                        "choices": [
                            {"name": "Dog", "value": "animal_dog"},
                            {"name": "Cat", "value": "animal_cat"},
                            {"name": "Penguin", "value": "animal_penguin"},
                        ],
                    },
                    {
                        "name": "only_smol",
                        "description": "Whether to show only baby animals",
                        "type": 5,
                        "required": False,
                    },
                ],
            }
            await ctx.send(json)
            resp = await self.httpSession.post(url, headers=headers, json=json)
        else:
            payload = RawJson
            await ctx.send(payload)
            resp = await self.httpSession.post(url, headers=headers, data=payload)
        await ctx.send(await resp.json())
        pass

    @commands.command()
    async def deleteCommand(self, ctx, Type: str, Id: int, GuildId: int = None):
        await ctx.send(Type)
        if Type == "global":
            url = f"https://discord.com/api/v8/applications/{self.appId}/commands/{Id}"
            await ctx.send(url)
            resp = await self.httpSession.delete(url, headers=self.authheader)
            text = await resp.text()
            await ctx.send(text if text != "" else "No content")
        elif Type == "local":
            url = f"https://discord.com/api/v8/applications/{self.appId}/guilds/{GuildId}/commands/{Id}"
            await ctx.send(url)
            resp = await self.httpSession.delete(url, headers=self.authheader)
            text = await resp.text()
            await ctx.send(text if text != "" else "No content")
        pass


def setup(bot: commands.Bot) -> None:
    bot.add_cog(SlashCommandsHelper(bot))
