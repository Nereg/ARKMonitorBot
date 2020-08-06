import sqlite3
import config
import logging
import discord
import sys
import ipaddress
import classes as c
import config
from inspect import currentframe
import mysql.connector
import asyncio
from discord.ext import commands 

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

def Debuger(name):
    #create logger
    log_obj = logging.getLogger(name)
    log_obj.setLevel(logging.DEBUG)
    #create message formatter
    formatter = logging.Formatter(fmt='%(asctime)s %(module)s,line: %(lineno)d %(levelname)8s | %(message)s', datefmt='%Y/%m/%d %H:%M:%S') 
    # console printer
    screen_handler = logging.StreamHandler(stream=sys.stdout) #stream=sys.stdout is similar to normal print
    screen_handler.setFormatter(formatter)
    logging.getLogger(name).addHandler(screen_handler)
    #integrate discord.py
    ds = logging.getLogger('discord')
    ds.setLevel(logging.DEBUG)
    ds.addHandler(screen_handler)
    #integrate async io 
    aio = logging.getLogger("asyncio")
    aio.setLevel(logging.DEBUG)
    aio.addHandler(screen_handler)
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
        return # if ip is correct
    servers = makeRequest('SELECT * FROM servers WHERE Ip=%s',(ip,))
    if (servers.__len__() > 0):
        return servers[0][0]
    try: 
        server = c.ARKServer(ip) # construct our classes
        playersList = c.PlayersList(ip)
        playersList.getPlayersList() # and get data
        server.GetInfo()
        debug.debug(f"Server {ip} is up!") # and debug
        if (server.version == ''  or server.version == None or '.' not in server.version):
            global message  
            message = await ctx.send(f"Server's name is too long and bot can't extract version from it. React with ✅ to continue with `(unknown)` version or react ⏹️ to not add this server.")
            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=lambda r,user: user.bot == False and r.message.id == message.id)
            except asyncio.TimeoutError:
                await message.edit('Timeout. Server won`t be added')
                return
            else:
                if (str(reaction.emoji) == '✅'):
                    await message.edit('OK!')
                    server.version = '(unknown)'
                elif (str(reaction.emoji) == '⏹️'):
                    await message.edit('OK! Rename server and come back!')
                    return
    except Exception as e: # if any exception
        debug.debug(e)
        await ctx.send(f'Server {ip} is offline! Tip: if you **certain** that server is up try `{ctx.prefix}ipfix`')
        return
    splitted = ip.split(':')
    makeRequest('INSERT INTO servers(Ip,ServerObj,PlayersObj,Port) VALUES (%s,%s,%s,%s)',[ip,server.toJSON(),playersList.toJSON(),splitted[1]])  # insert it into DB 
    Id = makeRequest('SELECT * FROM servers WHERE Ip=%s',(ip,))
    debug.debug(f'added server : {ip} with id : {Id[0][0]}!') # debug
    return Id[0][0]

def get_prefix(bot,message):
    conf = config.Config()
    guildId = message.guild.id
    data = makeRequest('SELECT * FROM settings WHERE GuildId=%s',(int(guildId),))
    if (data.__len__() <= 0 or data[0][2] == None):
        return conf.defaultPrefix
    else:
        return data[0][2]
    