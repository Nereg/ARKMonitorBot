import sqlite3
from config import Config
import logging
import discord
import sys
import ipaddress
import classes as c
import config
from inspect import currentframe
import mysql.connector

def  makeRequest(SQL,params=()):
    cfg = config.Config()
    mydb = mysql.connector.connect(
  host=cfg.dbHost,
  user=cfg.dbUser,
  password=cfg.dbPass,
  database=cfg.DB,buffered = True
    )
    mycursor = mydb.cursor()
    mycursor.execute(SQL, params)
    mydb.commit()
    try :
        return mycursor.fetchall()
    except mysql.connector.errors.InterfaceError :
        return []
#def makeRequest(SQL,params=[]): # wow universal !
#    conf = Config() # load config
#    conn = sqlite3.connect(conf.dbPath) # open connection to db in path from config 
#    cursor = conn.cursor() # old magic
#    cursor.execute(SQL,params) # really 
#    conn.commit() # I Ctrl + C and Ctrl + V this
#    results = cursor.fetchall() # from old code
#    conn.close() # close connection to DB!
#    return results # and return results

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
    try: 
        server = c.ARKServer(ip) # construct our classes
        playersList = c.PlayersList(ip)
        playersList.getPlayersList() # and get data
        server.GetInfo()
        debug.debug(f"Server {ip} is up!") # and debug
    except Exception as e: # if any exception
        debug.debug(e)
        await ctx.send(f'Server {ip} is offline!')
        return
    splitted = ip.split(':')
    makeRequest('INSERT INTO servers(Ip,ServerObj,PlayersObj,Port) VALUES (%s,%s,%s,%s)',[ip,server.toJSON(),playersList.toJSON(),splitted[1]])  # insert it into DB 
    Id = makeRequest('SELECT * FROM servers WHERE Ip=%s',(ip,))
    debug.debug(f'added server : {ip} with id : {Id[0][0]}!') # debug
    await ctx.send('Done!') # and reply
    return Id[0][0]

def get_prefix(bot,message):
    conf = Config()
    guildId = message.guild.id
    data = makeRequest('SELECT * FROM settings WHERE GuildId=%s',(int(guildId),))
    if (data.__len__() <= 0):
        return conf.defaultPrefix
    else:
        return data[0][2]
    