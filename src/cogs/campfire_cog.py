import cogs.utils.classes as c  # our classes
from cogs.utils.helpers import *  # our helpers
import config  # config
import discord  # main discord libary
from discord.ext import commands  # import commands extension
from discord.ext import tasks
import datetime
import enum


class Meat(enum.Enum):
    Default = 0
    Prime = 1
    Mutton = 2
    Fish = 3
    Fish_Prime = 4

    @classmethod  # now this method can be used like Meat.convert('0')
    def convert(self, str):
        types = [
            ["0", "Raw", "raw", "raw meat", "Raw meat", "Raw Meat"],
            ["prime", "Prime", "1", "prime meat", "Prime meat"],
            ["2", "mutton", "Mutton", "Sheep", "sheep"],
            ["3", "fish", "Fish"],
            ["4", "prime fish", "Prime fish"],
        ]
        if str in types[0]:
            return Meat.Default
        elif str in types[1]:
            return Meat.Prime
        elif str in types[2]:
            return Meat.Mutton
        elif str in types[3]:
            return Meat.Fish
        elif str in types[4]:
            return Meat.Fish_Prime
        else:
            return False

    def cookTime(self):
        if self == Meat.Default:
            return 20
        elif self == Meat.Prime:
            return 20
        elif self == Meat.Mutton:
            return 60
        elif self == Meat.Fish:
            return 20
        elif self == Meat.Fish_Prime:
            return 20
        else:
            raise NotImplementedError()


class Fuel(enum.Enum):
    Thatch = 0
    Wood = 1
    Sparkpowder = 2

    def burnTime(self):
        if self == Fuel.Thatch:
            return 7.5
        elif self == Fuel.Wood:
            return 30
        elif self == Fuel.Sparkpowder:
            return 60
        else:
            raise NotImplementedError()


class Campfire(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rate = 1
        self.cfg = config.Config()
        pass

    def calculate(self, meatCount: int, meatType: Meat, campCount: int = 1):
        import math

        # TODO: add check if all that meat will fit into one camp and if space will be left for fuel
        self.meatPerCamp = meatCount // campCount

        self.lefoverMeat = meatCount % campCount

        self.cookTime = (
            (meatCount * meatType.cookTime()) / campCount
        ) / self.rate  # in seconds (maybe)

        self.thatchPerCamp = math.ceil(self.cookTime / Fuel.Thatch.burnTime())
        self.totalThatch = self.thatchPerCamp * campCount

        self.woodPerCamp = math.ceil(self.cookTime / Fuel.Wood.burnTime())
        self.totalWood = self.woodPerCamp * campCount

        self.cookTimeMin = str(int(self.cookTime // 60)).zfill(2)
        self.cookTimeSec = str(int(self.cookTime - (int(self.cookTimeMin) * 60))).zfill(
            2
        )
        self.cookTimeHor = str(int(self.cookTime // 3600)).zfill(2)

    async def sendEmbed(self, ctx, title, name, value):
        time = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        emb = discord.Embed(title=title, timestamp=time.utcnow())
        emb.set_footer(
            text=f"Requested by {ctx.author.name} • Bot {self.cfg.version} • GPLv3 ",
            icon_url=ctx.author.display_avatar,
        )
        emb.add_field(name=name, value=value)
        ctx.send(embed=emb)
        return

    @commands.bot_has_permissions(
        add_reactions=True,
        read_messages=True,
        send_messages=True,
        manage_messages=True,
        external_emojis=True,
    )
    @commands.command()
    async def campfire(self, ctx, ammount: int = None, camps: int = 1):
        time = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        if ammount == None:
            emb = discord.Embed(title="Campfire rates:", timestamp=time.utcnow())
            emb.set_footer(
                text=f"Requested by {ctx.author.name} • Bot {self.cfg.version} • GPLv3 ",
                icon_url=ctx.author.display_avatar,
            )
            emb.set_thumbnail(
                url="https://static.wikia.nocookie.net/arksurvivalevolved_gamepedia/images/0/01/Campfire.png"
            )
            emb.add_field(name="Thatch burn time:", value="7.5 seconds", inline=False)
            emb.add_field(name="Wood burn time:", value="30 seconds", inline=False)
            emb.add_field(
                name="Cook time of any fish or meat:", value="20 seconds", inline=False
            )
            emb.add_field(name="Cook time of mutton:", value="1 minute", inline=False)
            await ctx.send(embed=emb)
            return
        if camps <= 0:
            await self.sendEmbed(
                ctx,
                "Oops!",
                "You can`t use 0 or negative numbers for `camps` parameter!",
                "Just don't. You can't cook something in 0 camps, can you?",
            )
            return
        self.calculate(ammount, Meat.Default, camps)
        emb = discord.Embed(title="Campfire", timestamp=time.utcnow())
        emb.set_footer(
            text=f"Requested by {ctx.author.name} • Bot {self.cfg.version} • GPLv3 ",
            icon_url=ctx.author.display_avatar,
        )
        if camps == 1:
            emb.add_field(
                name="Time:",
                value=f"{self.cookTimeHor}:{self.cookTimeMin}:{self.cookTimeSec}",
                inline=True,
            )
            emb.add_field(name="Thatch:", value=self.thatchPerCamp, inline=True)
            emb.add_field(name="Wood:", value=self.woodPerCamp, inline=False)
            emb.set_thumbnail(
                url="https://static.wikia.nocookie.net/arksurvivalevolved_gamepedia/images/0/01/Campfire.png"
            )
            await ctx.send(embed=emb)
            return
        else:
            emb.add_field(
                name="Time:",
                value=f"{self.cookTimeHor}:{self.cookTimeMin}:{self.cookTimeSec}",
                inline=False,
            )
            emb.add_field(
                name="Thatch (per camp):", value=self.thatchPerCamp, inline=False
            )
            emb.add_field(name="Wood (per camp):", value=self.woodPerCamp, inline=False)
            emb.add_field(name="Total thatch:", value=self.totalThatch, inline=False)
            emb.add_field(name="Total wood:", value=self.totalWood, inline=False)
            emb.set_thumbnail(
                url="https://static.wikia.nocookie.net/arksurvivalevolved_gamepedia/images/0/01/Campfire.png"
            )
            await ctx.send(embed=emb)
            return


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Campfire(bot))
