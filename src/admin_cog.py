from discord.ext import commands
import asyncio
import traceback
import discord
import inspect
import textwrap
import importlib
from contextlib import redirect_stdout
import io
import os
import re
import sys
import copy
import time
import subprocess
from typing import Union, Optional
from helpers import *
import json
# to expose to the eval command
import datetime
from collections import Counter
from discord.ext import tasks

class PerformanceMocker:
    """A mock object that can also be used in await expressions."""

    def __init__(self):
        self.loop = asyncio.get_event_loop()

    def permissions_for(self, obj):
        # Lie and say we don't have permissions to embed
        # This makes it so pagination sessions just abruptly end on __init__
        # Most checks based on permission have a bypass for the owner anyway
        # So this lie will not affect the actual command invocation.
        perms = discord.Permissions.all()
        perms.administrator = False
        perms.embed_links = False
        perms.add_reactions = False
        return perms

    def __getattr__(self, attr):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __repr__(self):
        return '<PerformanceMocker>'

    def __await__(self):
        future = self.loop.create_future()
        future.set_result(self)
        return future.__await__()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return self

    def __len__(self):
        return 0

    def __bool__(self):
        return False

class GlobalChannel(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return await commands.TextChannelConverter().convert(ctx, argument)
        except commands.BadArgument:
            # Not found... so fall back to ID + global lookup
            try:
                channel_id = int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f'Could not find a channel by ID {argument!r}.')
            else:
                channel = ctx.bot.get_channel(channel_id)
                if channel is None:
                    raise commands.BadArgument(f'Could not find a channel by ID {argument!r}.')
                return channel

class Admin(commands.Cog):
    """Admin-only commands that make the bot dynamic."""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()
        self.cmdCountUpdater.start()
        print('started cmd updater')

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author) or ctx.author.id == 277490576159408128
    async def run_process(self, command):
        try:
            process = await asyncio.create_subprocess_shell(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await process.communicate()
        except NotImplementedError:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await self.bot.loop.run_in_executor(None, process.communicate)

        return [output.decode() for output in result]

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @commands.command(pass_context=True, hidden=True, name='eval')
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code"""

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @commands.command(pass_context=True, hidden=True)
    async def repl(self, ctx):
        """Launches an interactive REPL session."""
        variables = {
            'ctx': ctx,
            'bot': self.bot,
            'message': ctx.message,
            'guild': ctx.guild,
            'channel': ctx.channel,
            'author': ctx.author,
            '_': None,
        }

        if ctx.channel.id in self.sessions:
            await ctx.send('Already running a REPL session in this channel. Exit it with `quit`.')
            return

        self.sessions.add(ctx.channel.id)
        await ctx.send('Enter code to execute or evaluate. `exit()` or `quit` to exit.')

        def check(m):
            return m.author.id == ctx.author.id and \
                   m.channel.id == ctx.channel.id and \
                   m.content.startswith('`')

        while True:
            try:
                response = await self.bot.wait_for('message', check=check, timeout=10.0 * 60.0)
            except asyncio.TimeoutError:
                await ctx.send('Exiting REPL session.')
                self.sessions.remove(ctx.channel.id)
                break

            cleaned = self.cleanup_code(response.content)

            if cleaned in ('quit', 'exit', 'exit()'):
                await ctx.send('Exiting.')
                self.sessions.remove(ctx.channel.id)
                return

            executor = exec
            if cleaned.count('\n') == 0:
                # single statement, potentially 'eval'
                try:
                    code = compile(cleaned, '<repl session>', 'eval')
                except SyntaxError:
                    pass
                else:
                    executor = eval

            if executor is exec:
                try:
                    code = compile(cleaned, '<repl session>', 'exec')
                except SyntaxError as e:
                    await ctx.send(self.get_syntax_error(e))
                    continue

            variables['message'] = response

            fmt = None
            stdout = io.StringIO()

            try:
                with redirect_stdout(stdout):
                    result = executor(code, variables)
                    if inspect.isawaitable(result):
                        result = await result
            except Exception as e:
                value = stdout.getvalue()
                fmt = f'```py\n{value}{traceback.format_exc()}\n```'
            else:
                value = stdout.getvalue()
                if result is not None:
                    fmt = f'```py\n{value}{result}\n```'
                    variables['_'] = result
                elif value:
                    fmt = f'```py\n{value}\n```'

            try:
                if fmt is not None:
                    if len(fmt) > 2000:
                        await ctx.send('Content too big to be printed.')
                    else:
                        await ctx.send(fmt)
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await ctx.send(f'Unexpected error: `{e}`')

    @commands.command(hidden=True)
    async def sudo(self, ctx, channel: Optional[GlobalChannel], who: discord.User, *, command: str):
        """Run a command as another user optionally in another channel."""
        msg = copy.copy(ctx.message)
        channel = channel or ctx.channel
        msg.channel = channel
        msg.author = channel.guild.get_member(who.id) or who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        #new_ctx._db = ctx._db
        await self.bot.invoke(new_ctx)

    @commands.command(hidden=True)
    async def do(self, ctx, times: int, *, command):
        """Repeats a command a specified number of times."""
        msg = copy.copy(ctx.message)
        msg.content = ctx.prefix + command

        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        #new_ctx._db = ctx._db

        for i in range(times):
            await new_ctx.reinvoke()

    @commands.command(hidden=True)
    async def sh(self, ctx, *, command):
        """Runs a shell command."""
        async with ctx.typing():
            stdout, stderr = await self.run_process(command)

        if stderr:
            text = f'stdout:\n{stdout}\nstderr:\n{stderr}'
        else:
            text = stdout

        try:
            await ctx.send(text)
        except Exception as e:
            await ctx.send(str(e))

    @commands.command(hidden=True)
    async def perf(self, ctx, *, command):
        """Checks the timing of a command, attempting to suppress HTTP and DB calls."""

        msg = copy.copy(ctx.message)
        msg.content = ctx.prefix + command

        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        new_ctx._db = PerformanceMocker()

        # Intercepts the Messageable interface a bit
        new_ctx._state = PerformanceMocker()
        new_ctx.channel = PerformanceMocker()

        if new_ctx.command is None:
            return await ctx.send('No command found')

        start = time.perf_counter()
        try:
            await new_ctx.command.invoke(new_ctx)
        except commands.CommandError:
            end = time.perf_counter()
            success = False
            try:
                await ctx.send(f'```py\n{traceback.format_exc()}\n```')
            except discord.HTTPException:
                pass
        else:
            end = time.perf_counter()
            success = True

        await ctx.send(f'Status: {ctx.tick(success)} Time: {(end - start) * 1000:.2f}ms')

    @commands.command()
    async def exec(self,ctx,sql):
        data = await makeAsyncRequest(sql)
        await ctx.send(data)
    
    @commands.command()
    async def setMessage(self, ctx, message):
        result = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=1')
        if (result.__len__() <= 0):
            await makeAsyncRequest('INSERT INTO settings(GuildId, Prefix, ServersId, Admins, Type, Aliases) VALUES (1,"","","",0,"")')
        await makeAsyncRequest('UPDATE settings SET Admins=%s WHERE GuildId=1',(message,))
        await ctx.send('Done!')

    @commands.command()
    async def deleteMessage(self, ctx, channelId : int, messageId : int):
        channel = self.bot.get_channel(channelId)
        if (channel == None):
            await ctx.send('Wrong channel id')
        else:
            try:
                message =  await channel.fetch_message(messageId)
            except BaseException as e:
                await ctx.send('error')
                await ctx.send(e)
                return
            await message.delete()
            await ctx.send('Done !')

    @commands.command()
    async def restart(self, ctx):
        await ctx.send('Good bye my friend!')
        exit(12121312)
        return

    @commands.command()
    async def deleteServer(self, ctx, serverIp : str):
        await deleteServer(serverIp)
    
    @commands.command()
    async def setCmdCountChannel(self, ctx, value : str = None, channel : discord.VoiceChannel = None):
        '''
        Sets channel to update count of commands used
        supports formatting of value string wich will be put into channel's name
        where the heck I will store this data ? i am so lazy to make another table and I hate sql and how it is painful to migrate to production
        why not create misc table lol and here it is :
        CREATE TABLE `bot`.`manager` ( `Id` INT NOT NULL AUTO_INCREMENT , `Type` INT NOT NULL , `Data` VARCHAR(9999) NOT NULL , PRIMARY KEY (`Id`)) ENGINE = InnoDB; 
        '''
        if (channel == None):
            await ctx.send('Channel is not selected or wrong!')
            return
        if (value == None):
            await ctx.send('You passed an empty string!')
            return
        if (not '{' in value):
            await ctx.send('Do you realy want to pass string witout format place?')
            return
        channels = await makeAsyncRequest('SELECT * FROM manager WHERE Type=0')
        for channelRecord in channels:
            data = json.loads(channelRecord[2])
            if int(data[0]) == channel.id:
                await ctx.send(f'You already have a message for that channel with id {channelRecord[0]}!')
                return 
        record = [int(channel.id),value]
        await makeAsyncRequest('INSERT INTO manager (Type,Data) VALUES (0,%s)',(json.dumps(record),))
        await ctx.send('Done!')
        return

    async def purge(self,ctx,value:int):
        servers = await makeAsyncRequest('SELECT Id FROM servers WHERE OfflineTrys >= %s',(value,))
        for server in servers:
            id = server[0]
            result = await deleteServer('',id)
            if(result != 0):
                await ctx.send(f'Smt went wrong with server {id}!')
        await ctx.send('Deleted servers!')
        return

    @commands.command()
    async def purgeServers(self, ctx, *argv):
        if (argv.__len__() <= 0):
            await ctx.send("Not every parameter was supplied!")
            return
        elif (str.isdigit(argv[0])):
            value = int(argv[0])
        else:
            await ctx.send(f"`{ argv[0]}` isn't a number!")
            return
        machedServers = await makeAsyncRequest('SELECT COUNT(*) FROM `servers` WHERE OfflineTrys >= %s',(value,))
        self.msg = await ctx.send(f'Do you really want to delete {machedServers[0][0]} servers?')
        await self.msg.add_reaction('✅')
        try:
            reaction,user = await self.bot.wait_for('reaction_add',timeout=100,check=lambda r,user: user != self.bot.user and r.message.id == self.msg.id)
        except asyncio.TimeoutError:
            try:
                await self.msg.clear_reactions()
                await self.msg.edit(content='The interactive menu was closed.',embed=None)
            except discord.errors.NotFound: # It was SO ANNOYING ! DONT DELET MESSAGES THERE ARE STOP BUTTON! (yeah I pasted this code from user space why not)
                return ''
        else:
            if (str(reaction.emoji) == '✅'):
                await ctx.send('Ok! Deleting!')
                await self.msg.clear_reactions()
                await self.purge(ctx,value)

    @commands.command()
    async def setServersCountChannel(self, ctx, value : str = None, channel : discord.VoiceChannel = None):
        if (channel == None):
            await ctx.send('Channel is not selected or wrong!')
            return
        if (value == None):
            await ctx.send('You passed an empty string!')
            return
        if (not '{' in value):
            await ctx.send('Do you realy want to pass string witout format place?')
            return
        channels = await makeAsyncRequest('SELECT * FROM manager WHERE Type=1')
        for channelRecord in channels:
            data = json.loads(channelRecord[2])
            if int(data[0]) == channel.id:
                await ctx.send(f'You already have a message for that channel with id {channelRecord[0]}!')
                return 
        record = [int(channel.id),value]
        await makeAsyncRequest('INSERT INTO manager (Type,Data) VALUES (1,%s)',(json.dumps(record),))
        await ctx.send('Done!')
        return
        

    @tasks.loop(seconds=20.0) 
    async def cmdCountUpdater(self):
        '''
        Well no excluding of commands and no order but I'll do with that
        '''
        print('entered cmd updater')
        channels = await makeAsyncRequest('SELECT * FROM manager WHERE Type=0') # get all record about channels we need to update
        commands = await makeAsyncRequest('SELECT * FROM commandsused') # get commands 
        total = await makeAsyncRequest('SELECT SUM(Uses) FROM commandsused') # get how much all commands are used
        total = total[0][0] # extract count of all commands used
        i=0 
        for channel in channels: # for each channel in DB
            cmd = commands[i] # get command
            data = json.loads(channel[2]) # load data
            print(data) # debug
            discordChannel = self.bot.get_channel(data[0]) # get channel 
            print(discordChannel) # debug
            if (discordChannel == None): # if channel is not found
                continue # skip 
            await discordChannel.edit(reason='Auto edit',name=data[1].format(cmd[1],int(cmd[2]),total)) # else edit name of the channel
            print('edited')
            i += 1 # increase i 

    @cmdCountUpdater.before_loop
    async def before_printer(self):
        print('waiting...')
        await self.bot.wait_until_ready() # wait until cache of bot is ready
