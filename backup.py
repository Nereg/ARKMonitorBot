import datetime
import os
import aiohttp # I am lazy to include requests
import asyncio
import json
from src import config
import subprocess # get output of commands
async def sendToWebhook(text,url):  
    if (url == None or url == ''):
        raise Exception()
    payload = f'content={text}'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload,headers=headers) as resp:
            return

def runCommand(cmd):
    try:
        result = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        asyncio.run(sendToWebhook(f'Something went wrong!\n```{e}```',cfg.backupWebhookUrl))

cfg = config.Config() # load config
asyncio.run(sendToWebhook('Entered backup script!',cfg.backupWebhookUrl))
time = datetime.datetime(2000,1,1,0,0,0,0)
time = time.utcnow()
months = time.strftime('%b-%m')
day = time.strftime('%d-%H') # get and format time
#container_name = 'arkdiscordbot_db_1' # set container name to use in commands
container_name = 'arkmonitorbot_db_1' # set container name to use in commands
password = cfg.dbPass # get DB password and user
user = cfg.dbUser
backup = f'docker exec {container_name} bash -c "touch /var/lib/mysql/{day}.sql && mysqldump -u {user} -p{password} bot > /var/lib/mysql/{day}.sql --protocol=TCP"' # dumps all tables of bot DB in {day.sql}
copy = f'mkdir -p ~/backup/{months} && docker cp {container_name}:/var/lib/mysql/{day}.sql ~/backup/{months}' # makes backup folder and copyes backup from container to that folder
send = f'cd ~/backup/ && git add ~/backup/{months}/{day}.sql && git commit . -m "Backup from main server ({time.strftime("%Y.%m.%d.%H")})" && git push --set-upstream origin master' # commints and pushes backed up copy of DB
runCommand(backup) # run constucted commands
runCommand(copy)
runCommand(send)
asyncio.run(sendToWebhook('Backed up!',cfg.backupWebhookUrl))