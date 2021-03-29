import datetime
import os
from src import config
cfg = config.Config() # load config
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
os.system(backup) # run constucted commands
os.system(copy)
os.system(send)