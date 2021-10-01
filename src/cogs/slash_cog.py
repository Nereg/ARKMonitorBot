from discord.ext import commands
import discord
import aiohttp

class Slash(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.appId = 727114852245569545
        self.cfg = bot.cfg
        self.token = self.cfg.token
        self.authheader = {"Authorization": f"Bot {self.token}"}
    
    async def cog_before_invoke(self, ctx):
        # if we have no http pool
        if (getattr(self,'httpSession',None) == None):
            # create it
            self.httpSession = aiohttp.ClientSession()

    @commands.command()
    async def validateSlash(self,ctx):
        # get local slash commands
        resp = await self.httpSession.get(f'https://discord.com/api/v8/applications/{self.appId}/guilds/{ctx.guild.id}/commands',
                                         headers=self.authheader)
        #await ctx.send(resp)
        # if 200 http code
        if (resp.status == 200):
            # construct embed
            embed = discord.Embed()
            embed.title = 'Everything OK!'
            embed.description = 'You have everything set up for use of new slash commands.'
            embed.colour = discord.Colour.green()
        # if 403 we don't have new OAuth2 scope
        elif (resp.status == 403):
            # construct error with reinvite link
            embed = discord.Embed()
            embed.title = 'You need to re-invite the bot!'
            embed.add_field(name = 'Discord requires re-inviting for some older servers.',
                            value = 'You **should** re-invite the bot with [this](https://discord.com/oauth2/authorize?client_id=713272720053239808&scope=bot%20applications.commands&permissions=1141189696) link!')
            embed.colour = discord.Colour.red()
        # something bad happened 
        else:
            # construct error message
            embed = discord.Embed()
            embed.title = 'Oops, something went wrong on our side.'
            embed.description = 'Please retry in a few minutes. Report this issue if it persists'
            embed.colour = discord.Colour.green()
        # get permissions for current user
        perms = ctx.channel.permissions_for(ctx.author) 
        # if the user can use slash commands
        if (perms.use_slash_commands):
            embed2 = discord.Embed()
            embed2.title = 'You can execute slash commands!'
            embed2.description = "I've cheched your permissions and you can execute slash command in current channel."
            embed2.colour = discord.Colour.green()
        else:
            embed2 = discord.Embed()
            embed2.title = "You **can't** execute slash commands!"
            embed2.description = "I've cheched your permissions and you **can't** execute slash command in current channel. Please check your permissions. You should turn on [Use Application Commands](https://cdn.discordapp.com/attachments/801142940595912728/893528552505483364/unknown.png) permission."
            embed2.colour = discord.Colour.red()
        await ctx.send(embeds=[embed, embed2])

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Slash(bot))