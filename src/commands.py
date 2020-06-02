from helpers import * # all our helpers
import classes as c # all our classes
import discord # main discord lib
import menus as m
import server_cmd as server # import /server command module (see server_cmd.py)

async def list_servers(ctx): # /list entrypoint
    servers = '' # string with list of servers
    data = makeRequest('SELECT * FROM Servers') # select all servers from DB
    i = 1 # i (yeah classic)
    for result in data: # fro each record in DB
        server = c.ARKServer.fromJSON(result[1]) # construct our class
        online = bool(data[0][3]) # exstarct last online state 
        emoji = ':green_circle:' if online else ':red_circle:' # if last online is tru green circle else (if offline) red
        servers += f'{i}. {server.name}  {emoji}  ||{server.ip}|| \n' # construct line and add it to all strings
        i += 1 
    # send message
    await ctx.send(f''' 
Список добавленных серверов :
{servers}
    ''')


            