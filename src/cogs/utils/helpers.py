import sqlite3
import config
import logging
import discord
import sys
import ipaddress
from . import classes as c
import config
import mysql.connector
import asyncio
from discord.ext import commands
import aiomysql
import json
import random
import aiohttp


def makeRequest(SQL, params=()):
    cfg = config.Config()
    mydb = mysql.connector.connect(
        host=cfg.dbHost,
        user=cfg.dbUser,
        password=cfg.dbPass,
        port=3306,
        database=cfg.DB, buffered=True
    )
    mycursor = mydb.cursor()
    mycursor.execute(SQL, params)
    mydb.commit()
    try:
        return mycursor.fetchall()
    except mysql.connector.errors.InterfaceError:
        return []


async def makeAsyncRequest(SQL, params=()):
    cfg = config.Config()
    conn = await aiomysql.connect(host=cfg.dbHost, port=3306,
                                  user=cfg.dbUser, password=cfg.dbPass,
                                  db=cfg.DB, loop=asyncio.get_running_loop())  
                                  # https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.get_running_loop
    async with conn.cursor() as cur:
        await cur.execute(SQL, params)
        result = await cur.fetchall()
        await conn.commit()
    conn.close()
    return result


def Debuger(name):
    # create logger

    log_obj = logging.getLogger(name)
    log_obj.setLevel(logging.DEBUG)
    if (log_obj.hasHandlers()):
        log_obj.handlers.clear()
    # create message formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s %(module)s,line: %(lineno)d %(levelname)8s | %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
    # console printer
    # stream=sys.stdout is similar to normal print
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logging.getLogger(name).addHandler(screen_handler)
    # integrate discord.py
    ds = logging.getLogger('discord')
    ds.setLevel(logging.INFO)
    ds.addHandler(screen_handler)
    # integrate async io
    #aio = logging.getLogger("asyncio")
    # aio.setLevel(logging.DEBUG)
    # aio.addHandler(screen_handler)
    # and return
    return log_obj


def IpCheck(Ip):
    try:  # try just for fun
        splitted = Ip.split(':')
        if (splitted.__len__() <= 1):  # if port is not present
            return False
        try:  # if
            ipaddress.ip_address(splitted[0])  # extracted ip address
        except:  # is not valid ip address
            return False  # return false
        # exstract port and convert to int (if not int exeption is cathced)
        port = int(splitted[1])
        if (port > 65535 or port <= 0):  # http://stackoverflow.com/questions/113224/ddg#113228
            return False  # if port is not a valid port return false
        return True  # if all if passed return true
    except:
        return False  # if any error return false


async def fixIp(ip: str):
    '''
    Replaces wrong ip:port pair with correct ip:port pair
    (If original port is a game port of a server on that ip)
    Else returns false 
    '''
    splitted = ip.split(':')  # split ip:port pair
    ip = splitted[0]  # set ip to first chunk of ip string
    port = int(splitted[1])  # set port to second chunk of ip string
    HEADERS = {
        'User-Agent': "Magic Browser"
    }
    # https://stackoverflow.com/questions/27340334/how-to-request-steam-api-over-10000-times-with-php-or-javascript 
    # let's hope that we wouldn't hit any ratelimits
    # get data from steam API
    async with aiohttp.request("GET", f'http://api.steampowered.com/ISteamApps/GetServersAtAddress/v0001?addr={ip}', headers=HEADERS) as resp:
        response = await resp.json()  # get and parse JSON data from Steam
        # print(response)
        # print(f'http://api.steampowered.com/ISteamApps/GetServersAtAddress/v0001?addr={ip}')
        # if request is successful and we have more that 0 servers
        if (bool(response['response']['success']) and response['response']['servers'].__len__() > 0):
            # here we will match game port we have to query port the rest of the bot needs
            # for each server in response
            for server in response['response']['servers']:
                if (server['gameport'] == port):  # if game port matches of that in the response
                    # return address of the server (and pray that it is the server user intended to add)
                    return server['addr']
            return False  # if no servers matched return false
        else:  # if failed
            return False  # return false


async def AddServer(ip, ctx):
    '''
    Adds a server to the DB. 
    Checks for common error and, if possible, fixes them or notifies user
    If succesful returns id of added server else returns None
    '''
    debug = Debuger('AddServer')
    await ctx.trigger_typing()
    if (IpCheck(ip) != True):  # check IP address
        if ('>' in ip or '<' in ip):  # if we have < or > in string
            # tell the user that they aren't needed
            await ctx.send('You don`t need those <>!')
            return  # return
        # debug.debug(f'Wrong IP : {ip}') # debug
        await ctx.send('Something is wrong with **IP**!')  # and reply to user
        return  # return because ip is incorrect
    # search for already added server in DB
    servers = await makeAsyncRequest('SELECT * FROM servers WHERE Ip=%s', (ip,))
    if (servers.__len__() > 0):  # if we found one
        return servers[0][0]  # return it's id
    try:  # else
        server = c.ARKServer(ip)  # construct our classes
        playersList = c.PlayersList(ip)
        await playersList.AgetPlayersList()  # and get data
        await server.AGetInfo()
        if (not server.isARK):  # if the server isn't an ARK server
            # send an error about it
            await ctx.send(f'This server is not ARK! Possible Steam AppId: {server.game_id}')
            return  # and return
        # debug.debug(f"Server {ip} is up!") # and debug
    except Exception as e:  # if any exception
        # debug.debug(e)
        # let's try smth different
        newIp = await fixIp(ip)  # let's try to fix the ip
        # print(bool(newIp))
        if (newIp):  # if we fixed the ip
            try:  # try to add it one more time
                server = c.ARKServer(newIp)  # construct our classes
                playersList = c.PlayersList(newIp)
                await playersList.AgetPlayersList()  # and get data
                await server.AGetInfo()
                if (not server.isARK):  # if the server isn't an ARK server
                    # send an error about it
                    await ctx.send(f'This server is not ARK! Possible Steam AppId: {server.game_id}')
                    return  # and return
                ip = newIp  # I don't want to mess with the rest of the code
            except:  # if exeption
                # send an error message
                await ctx.send(f'Server `{discord.utils.escape_mentions(newIp)}` is offline! Tip: if you **certain** that server is up try `{ctx.prefix}ipfix`')
                return
        else:
            # send an error message
            await ctx.send(f'Server `{discord.utils.escape_mentions(ip)}` is offline! Tip: if you **certain** that server is up try `{ctx.prefix}ipfix`')
            return
    splitted = ip.split(':')  # if we got all the data and ip is correct
    # insert it into DB
    await makeAsyncRequest('INSERT INTO servers(Ip,ServerObj,PlayersObj,Port) VALUES (%s,%s,%s,%s)', [ip, server.toJSON(), playersList.toJSON(), splitted[1]])
    # search it's id
    Id = await makeAsyncRequest('SELECT * FROM servers WHERE Ip=%s', (ip,))
    debug.debug(f'added server : {ip} with id : {Id[0][0]}!')  # debug
    return Id[0][0]  # and return id of a new server


async def get_prefix(bot, message):
    '''
    returns prefix for a guild
    '''
    conf = config.Config()  # load our config
    guildId = message.guild.id  # get id of the guild
    # search in DB for settings of the guild
    data = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=%s', (int(guildId),))
    # if settings of server aren't found or prefix is none
    if (data.__len__() <= 0 or data[0][2] == None):
        return conf.defaultPrefix  # return default prefix
    else:
        return data[0][2]  # return prefix of the guild


async def getAlias(serverId, guildId, serverIp=''):
    if (serverIp != ''):
        serverId = await makeAsyncRequest('SELECT Id FROM servers WHERE Ip=%s', (serverIp,))
        serverId = serverId[0][0]
    settings = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=%s', (guildId,))
    if (settings[0][6] == None or settings[0][6] == ''):
        return ''
    else:
        aliases = json.loads(settings[0][6])
        if (serverId in aliases):
            mainIndex = aliases.index(serverId)
            return aliases[mainIndex+1]
        else:
            return ''


async def stripVersion(server, name=''):
    '''
    Return name of server but without server's version
    Parameters:
    server - ARKServer object
    Returns:
    str - name of the server with stripped version 
    '''
    if(name == ''):  # if we have no name to work with
        # get index of - (version) part with data from class
        name = server.name.find(f'- ({server.version})')
        name = server.name[:name].strip()  # set stripped version
    else:  # if we have just server's name
        first = name.find('(')  # split out version
        second = name.rfind(')')
        if (second == -1 or first == -1):  # if version is not found
            name = name  # return just name
        else:  # if version is found
            name = name[:first-2].strip()  # set stripped name
    return name  # return stripped name


async def sendToMe(text, bot, ping=False):
    '''
    Sends a text to Me the creator of this bot
    If ping is True it will ping me
    '''
    cfg = config.Config()
    try:
        # get our guild
        guild = bot.get_guild(cfg.logsGuildId)
        if (guild == None):
            print(f'Can`t get guild {cfg.logsGuildId}!')
            print(text)
            return
        # get channel for logs
        channel = guild.get_channel(cfg.logsChannelId)
        if (channel == None):
            print(f'Can`t get channel {cfg.logsChannelId}!')
            print(text)
            return
        # send message
        await channel.send(text)
        # if we need to ping me
        if (ping):
            # thanks intents I hate you
            await channel.send('<@277490576159408128>')
    except AttributeError:
        print("No permissions in 874715094645346395!")
        print(text)
        return
    except BaseException as e:
        print('exeption in sendToMe')
        print(e)
        print(text)
        return


async def deleteServer(serverIp, Id=-1):
    ''' 
    Delets server from DB by it's ip
    Parameters:
    serverIp - str - server's ip 
    Id - int - server's id (optional Ip is ignored if supplied)
    returns - int - 1 if failed 0 othervise
    '''
    if(Id == -1):
        server = await makeAsyncRequest('SELECT * FROM servers WHERE Ip=%s', (serverIp,))
        if (server.__len__() <= 0):
            return 1
        serverId = server[0][0]
    else:
        serverId = Id
    # print(serverId)
    notifications = await makeAsyncRequest('SELECT * FROM notifications')
    settings = await makeAsyncRequest('SELECT * FROM settings')
    automessages = await makeAsyncRequest('SELECT * FROM automessages WHERE ServerId=%s', (serverId,))
    for notification in notifications:
        try:
            ids = json.loads(notification[4])
        except BaseException:
            continue
        if (serverId in ids):
            ids.remove(serverId)
            await makeAsyncRequest('UPDATE notifications SET ServersIds=%s WHERE Id=%s', (json.dumps(ids), notification[0],))
            #print(f'Changed notification record {notification[0]} to {json.dumps(ids)}')
    for setting in settings:
        try:
            ids = json.loads(setting[3])
        except BaseException:
            continue
        if (serverId in ids):
            ids.remove(serverId)
            await makeAsyncRequest('UPDATE settings SET ServersId=%s WHERE Id=%s', (json.dumps(ids), setting[0],))
            # print(f'Changed settings for server {}')
    if (automessages.__len__() > 0):
        for message in automessages:
            await makeAsyncRequest('DELETE FROM automessages WHERE Id=%s', (message[0],))
    await makeAsyncRequest('DELETE FROM servers WHERE Id=%s', (serverId,))
    return 0


def randomColor():
    '''Picks random colors for embed'''
    colors = [discord.Color.red(), discord.Color.blue(
    ), discord.Color.from_rgb(255, 255, 0)]  # red blue and yellow
    return random.choice(colors)


def split2K(message, newLine=False):  # TODO : test this
    '''
    Splits a string over 2k symbols to less that 2k chunks to send them (discord emoji aware)
    If newLine is True it splits only on newlines
    Returns array with strings to send one ofter another
    '''
    length = message.__len__()  # get length of message
    if(length < 2000):  # if it is under 2k
        return [message]  # just send it
    else:  # that's where the FUN begins !
        result = []
        if (newLine):
            chunks = message.split('\n')
            megachunk = ''  # will hold so many chunks before it is over 2k
            for chunk in chunks:
                if chunk.__len__() >= 2000:  # oh shit
                    # 100% it would go into infinite recursion sometimes
                    subresult = split2K(chunk)
                    for bit in subresult:  # add every bit from subresult in our result
                        result.append(bit)  # add
                        continue
                else:  # this chunk is under 2k
                    testMegachunk = megachunk + chunk  # we will add it to iur mega chunk
                    if (testMegachunk.__len__() >= 2000):  # if our test super chunk is over 2k
                        result.append(megachunk)  # add to result
                        megachunk = ''  # empty mega chunk
                        continue
                    else:
                        megachunk = testMegachunk  # test chunk is our new megachunk
                        continue
        else:  # just split however code decides
            i = 0
            n = 1999
            while i < len(message):
                if i+n < len(message):
                    result.append(message[i:i+n])
                else:
                    result.append(message[i:len(message)])
                i += n
        return result


def sendOver2K(bot, ctx, message):
    '''
    Sends message over 2k symbols with current ctx using split2K function
    '''
    return
