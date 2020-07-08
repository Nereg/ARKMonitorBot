import schedule
import time
from helpers import *
import a2s
import classes as c
import config as cfg

def job():
    print('entered task!')
    servers = makeRequest('SELECT * FROM servers')
    for server in servers:
        ip = server[1]
        try:
            serverObj = c.ARKServer(ip).GetInfo()
            playersList = c.PlayersList(ip).getPlayersList()
            makeRequest('UPDATE servers SET ServerObj=%s , PlayersObj=%s , LastOnline=1 WHERE Ip =%s',(serverObj.toJSON(),playersList.toJSON(),ip))
            print(f'Updated record for online server: {ip}')
        except:
            makeRequest('UPDATE servers SET LastOnline=0, OfflineTrys=%s  WHERE Ip =%s',(server[6]+1,ip))
            print(f'Updated record for offline server: {ip}')
            
schedule.every(5).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)


#["Traceback (most recent call last):\n", "  File \"/usr/local/lib/python3.7/site-packages/mysql/connector/connection_cext.py\", line 489, in cmd_query\n    raw_as_string=raw_as_string)\n", "_mysql_connector.MySQLInterfaceError: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near ')' at line 1\n", "\nDuring handling of the above exception, another exception occurred:\n\n", "Traceback (most recent call last):\n", "  File \"/usr/local/lib/python3.7/site-packages/discord/ext/commands/core.py\", line 83, in wrapped\n    ret = await coro(*args, **kwargs)\n", "  File \"/app/src/commands.py\", line 37, in list\n    data = makeRequest(statement)\n", "  File \"/app/src/helpers.py\", line 24, in makeRequest\n    mycursor.execute(SQL, params)\n", "  File \"/usr/local/lib/python3.7/site-packages/mysql/connector/cursor_cext.py\", line 266, in execute\n    raw_as_string=self._raw_as_string)\n", "  File \"/usr/local/lib/python3.7/site-packages/mysql/connector/connection_cext.py\", line 492, in cmd_query\n    sqlstate=exc.sqlstate)\n", "mysql.connector.errors.ProgrammingError: 1064 (42000): You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near ')' at line 1\n", "\nThe above exception was the direct cause of the following exception:\n\n", "Traceback (most recent call last):\n", "  File \"/usr/local/lib/python3.7/site-packages/discord/ext/commands/bot.py\", line 892, in invoke\n    await ctx.command.invoke(ctx)\n", "  File \"/usr/local/lib/python3.7/site-packages/discord/ext/commands/core.py\", line 797, in invoke\n    await injected(*ctx.args, **ctx.kwargs)\n", "  File \"/usr/local/lib/python3.7/site-packages/discord/ext/commands/core.py\", line 92, in wrapped\n    raise CommandInvokeError(exc) from exc\n", "discord.ext.commands.errors.CommandInvokeError: Command raised an exception: ProgrammingError: 1064 (42000): You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near ')' at line 1\n"]