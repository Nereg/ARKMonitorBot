from helpers import * # all our helpers
import classes as c # all our classes
import discord # main discord lib
import menus as m
import server_cmd as server # import /server command module (see server_cmd.py)
import json

async def list_servers(ctx): # /list entrypoint
    servers = '' # string with list of servers
    l = c.Translation()
    if ctx.guild == None : 
        GuildId = ctx.channel.id
        Type = 1
    else:
        GuildId = ctx.guild.id
        Type = 0
    data = makeRequest('SELECT * FROM settings WHERE GuildId=%s AND Type=%s',(GuildId,Type))
    if (data[0][3] == None or data[0][3] == 'null'):
        await ctx.send(l.l['no_servers_added'].format(ctx.prefix))
        return
    else:
        Servers = json.loads(data[0][3]) #remove()
    statement = "SELECT * FROM servers WHERE Id IN ({})".format(', '.join(['{}'.format(Servers[i]) for i in range(len(Servers))]))
    data = makeRequest(statement)
    i = 1 # i (yeah classic)
    for result in data: # fro each record in DB
        server = c.ARKServer.fromJSON(result[4]) # construct our class
        online = bool(result[6]) # exstarct last online state 
        emoji = ':green_circle:' if online else ':red_circle:' # if last online is tru green circle else (if offline) red
        servers += f'{i}. {server.name}  {emoji}  ||{server.ip}|| \n' # construct line and add it to all strings
        i += 1 
    # send message
    await ctx.send(f''' 
Список добавленных серверов :
{servers}
    ''')


            