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
            makeRequest('UPDATE servers SET ServerObj=%s , PlayersObj=%s WHERE Ip =%s',(serverObj.toJSON(),playersList.toJSON(),ip))
            print(f'Updated record for online server: {ip}')
        except:
            makeRequest('UPDATE servers SET LastOnline=0, OfflineTrys=%s  WHERE Ip =%s',(server[6]+1,ip))
            print(f'Updated record for offline server: {ip}')
            
schedule.every(5).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)