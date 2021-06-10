import datetime
import os
import aiohttp  # I am lazy to include requests
import asyncio
import json
from src import config
import subprocess  # get output of commands


async def sendToWebhook(text, url):
    if (url == None or url == ''):
        raise Exception()
    payload = f'content={text}'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=headers) as resp:
            return


def runCommand(cmd):
    try:
        result = subprocess.check_output(cmd, shell=True)
        return result
    except subprocess.CalledProcessError as e:
        asyncio.run(sendToWebhook(
            f'Something went wrong!\n```{e}```', cfg.backupWebhookUrl))


cfg = config.Config()  # load config
asyncio.run(sendToWebhook('Entered backup script!', cfg.backupWebhookUrl))
time = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
time = time.utcnow()
months = time.strftime('%b-%m')
day = time.strftime('%d-%H')  # get and format time
# container_name = 'arkdiscordbot_db_1' # set container name to use in commands
container_name = 'arkmonitorbot_db_1'  # set container name to use in commands
password = cfg.dbPass  # get DB password and user
user = cfg.dbUser
# dumps all tables of bot DB in {day.sql}
backup = f"docker exec {container_name} bash -c 'touch /var/lib/mysql/{day}.sql && mysqldump -u {user} -p{password} bot > /var/lib/mysql/{day}.sql --protocol=TCP'"
#backup = ['docker', 'exec', f'{container_name}', 'bash', '-c', f"'touch /var/lib/mysql/{day}.sql'", '&&', 'mysqldump', '-u', f'{user}', f'-p{password}', 'bot', '>', f'/var/lib/mysql/{day}.sql', "--protocol=TCP'"]
# makes backup folder and copyes backup from container to that folder
copy = f'mkdir -p ~/backup/{months} && docker cp {container_name}:/var/lib/mysql/{day}.sql ~/backup/{months}'
# commints and pushes backed up copy of DB
send = f'cd ~/backup/ && git add ~/backup/{months}/{day}.sql && git commit . -m "Backup from main server ({time.strftime("%Y.%m.%d.%H")})" && git push --set-upstream origin master'
runCommand(backup)  # run constucted commands
runCommand(copy)
runCommand(send)
asyncio.run(sendToWebhook(
    f'`Df` output:\n{runCommand("df -h").decode("UTF-8")}', cfg.backupWebhookUrl))
asyncio.run(sendToWebhook('Backed up!', cfg.backupWebhookUrl))
