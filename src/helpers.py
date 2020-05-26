import sqlite3
from config import Config
import logging
import discord
import sys
import ipaddress

def makeRequest(SQL,params=[]): # wow universal !
    conf = Config() # load config
    conn = sqlite3.connect(conf.dbPath) # open connection to db in path from config 
    cursor = conn.cursor() # old magic
    cursor.execute(SQL,params) # really 
    conn.commit() # I Ctrl + C and Ctrl + V this
    results = cursor.fetchall() # from old code
    conn.close() # close connection to DB!
    return results # and return results

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

