import sqlite3
import config
import logging
import discord
import sys
import ipaddress
import classes as c
import config
import mysql.connector
import asyncio
from discord.ext import commands 
import aiomysql
import json
import random

def  makeRequest(SQL,params=()):
    cfg = config.Config()
    mydb = mysql.connector.connect(
  host=cfg.dbHost,
  user=cfg.dbUser,
  password=cfg.dbPass,
  port=3306,
  database=cfg.DB,buffered = True
    )
    mycursor = mydb.cursor()
    mycursor.execute(SQL, params)
    mydb.commit()
    try :
        return mycursor.fetchall()
    except mysql.connector.errors.InterfaceError :
        return []

async def  makeAsyncRequest(SQL,params=()):
    cfg = config.Config()
    conn = await aiomysql.connect(host=cfg.dbHost, port=3306,
                                      user=cfg.dbUser, password=cfg.dbPass,
                                      db=cfg.DB, loop=asyncio.get_running_loop()) #https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.get_running_loop
    async with conn.cursor() as cur:
        await cur.execute(SQL,params)
        result = await cur.fetchall()
        await conn.commit()
    conn.close()
    return result

def Debuger(name):
    #create logger

    log_obj = logging.getLogger(name)
    log_obj.setLevel(logging.DEBUG)    
    if (log_obj.hasHandlers()):
        log_obj.handlers.clear()
    #create message formatter
    formatter = logging.Formatter(fmt='%(asctime)s %(module)s,line: %(lineno)d %(levelname)8s | %(message)s', datefmt='%Y/%m/%d %H:%M:%S') 
    # console printer
    screen_handler = logging.StreamHandler(stream=sys.stdout) #stream=sys.stdout is similar to normal print
    screen_handler.setFormatter(formatter)
    logging.getLogger(name).addHandler(screen_handler)
    #integrate discord.py
    ds = logging.getLogger('discord')
    ds.setLevel(logging.INFO)
    ds.addHandler(screen_handler)
    #integrate async io 
    #aio = logging.getLogger("asyncio")
    #aio.setLevel(logging.DEBUG)
    #aio.addHandler(screen_handler)
    #and return
    return log_obj

def IpCheck(Ip):
    try: # try just for fun
        splitted = Ip.split(':')
        if (splitted.__len__() <=1): #if port is not present
            return False
        try: #if
            ipaddress.ip_address(splitted[0]) #extracted ip address
        except: #is not valid ip address
            return False # return false
        port = int(splitted[1]) #exstract port and convert to int (if not int exeption is cathced)
        if (port > 65535 or port <= 0): # http://stackoverflow.com/questions/113224/ddg#113228
            return False #if port is not a valid port return false
        return True # if all if passed return true
    except:
        return False # if any error retunr false


async def AddServer(ip,ctx):
    debug = Debuger('AddServer')
    if (IpCheck(ip) != True): # check IP address (see helpers.py)
        debug.debug(f'Wrong IP : {ip}') # debug
        await ctx.send('Something is wrong with **IP**!') # and reply to user
        return # if ip is incorrect
    servers = makeRequest('SELECT * FROM servers WHERE Ip=%s',(ip,))
    if (servers.__len__() > 0):
        return servers[0][0]
    try: 
        server = c.ARKServer(ip) # construct our classes
        playersList = c.PlayersList(ip)
        await playersList.AgetPlayersList() # and get data
        await server.AGetInfo()
        if (not server.isARK):
            await ctx.send(f'This server is not ARK! Possible Steam AppId: {server.game_id}')
            return
        #debug.debug(f"Server {ip} is up!") # and debug
    except Exception as e: # if any exception
        debug.debug(e)
        await ctx.send(f'Server {ip} is offline! Tip: if you **certain** that server is up try `{ctx.prefix}ipfix`')
        return
    splitted = ip.split(':')
    await makeAsyncRequest('INSERT INTO servers(Ip,ServerObj,PlayersObj,Port) VALUES (%s,%s,%s,%s)',[ip,server.toJSON(),playersList.toJSON(),splitted[1]])  # insert it into DB 
    Id = await makeAsyncRequest('SELECT * FROM servers WHERE Ip=%s',(ip,))
    debug.debug(f'added server : {ip} with id : {Id[0][0]}!') # debug
    return Id[0][0]

async def get_prefix(bot,message):
    conf = config.Config()
    guildId = message.guild.id
    data = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=%s',(int(guildId),))
    if (data.__len__() <= 0 or data[0][2] == None):
        return conf.defaultPrefix
    else:
        return data[0][2]

async def getAlias(serverId,guildId,serverIp=''):
    if(serverIp != ''):
        serverId = await makeAsyncRequest('SELECT Id FROM servers WHERE Ip=%s',(serverIp,))
        serverId = serverId[0][0]
    settings = await makeAsyncRequest('SELECT * FROM settings WHERE GuildId=%s',(guildId,))
    if (settings[0][6] == None or settings[0][6] == ''):
        return ''
    else:
        aliases = json.loads(settings[0][6])
        if (serverId in aliases):
            mainIndex = aliases.index(serverId)
            return aliases[mainIndex+1]
        else:
            return ''

async def stripVersion(server):
    '''
    Return name of server but without server's version
    Parameters:
    server - ARKServer object
    Returns:
    str - name of the server with stripped version 
    '''
    name = server.name.find(f'- ({server.version})')
    name = server.name[:name].strip()
    return name

async def sendToMe(text,bot):
    '''
    Sends a text to Me the creator of this bot
    '''
    try:
        meUser = bot.get_user(277490576159408128)
        meDM = await meUser.create_dm()
        await meDM.send(text)
    except BaseException as e:
        print('exeption in sendToMe')
        print(e)
        return

async def deleteServer(serverIp):
    ''' 
    Delets server from DB by it's ip
    Parameters:
    serverIp - str - server's ip 
    returns - int - 1 if failed 0 othervise
    '''
    server = await makeAsyncRequest('SELECT * FROM servers WHERE Ip=%s',(serverIp,))
    if (server.__len__() <=0 ):
        return 1
    else:
        serverId = server[0][0]
        #print(serverId)
        notifications = await makeAsyncRequest('SELECT * FROM notifications')
        settings = await makeAsyncRequest('SELECT * FROM settings')
        automessages = await makeAsyncRequest('SELECT * FROM automessages WHERE ServerId=%s',(serverId,))
        for notification in notifications:
            try:
                ids = json.loads(notification[4])
            except BaseException:
                continue
            if (serverId in ids):
                ids.remove(serverId)
                await makeAsyncRequest('UPDATE notifications SET ServersIds=%s WHERE Id=%s',(json.dumps(ids),notification[0],))
                #print(f'Changed notification record {notification[0]} to {json.dumps(ids)}')
        for setting in settings:
            try:
                ids = json.loads(setting[3])
            except BaseException:
                continue
            if (serverId in ids):
                ids.remove(serverId)
                await makeAsyncRequest('UPDATE settings SET ServersId=%s WHERE Id=%s',(json.dumps(ids),setting[0],))
                #print(f'Changed settings for server {}')
        if (automessages.__len__() > 0):
            for message in automessages:
                await makeAsyncRequest('DELETE FROM automessages WHERE Id=%s',(message[0],))
        await makeAsyncRequest('DELETE FROM servers WHERE Id=%s',(serverId,))
        return 0

def randomColor():
    '''Picks random colors for embed'''
    colors = [discord.Color.red(),discord.Color.blue(),discord.Color.from_rgb(255,255,0)] # red blue and yellow
    return random.choice(colors)

def split2K(message,newLine=False):
    '''
    Splits a string over 2k symbols to less that 2k chunks to send them (discord emoji aware)
    If newLine is True it splits only on newlines
    Returns array with strings to send one ofter another
    '''
    length = message.__len__() # get length of message
    if(length < 2000): # if it is under 2k
        return [message] # just send it
    else:
        
    return

def sendOver2K(bot,ctx,message):
    '''
    Sends message over 2k symbols with current ctx using split2K function
    '''
    return
