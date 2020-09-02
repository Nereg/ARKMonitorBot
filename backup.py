import datetime
import os

time = datetime.datetime(2000,1,1,0,0,0,0)
time = time.utcnow()
months = time.strftime('%b-%m')
day = time.strftime('%d-%H')
container_name = 'arkmonitorbot_db_1'
password = 'YOUR_PASSWORD'
backup = f'docker exec {container_name} bash -c "touch /var/lib/mysql/{day}.sql && mysqldump -u root -p{password} bot > /var/lib/mysql/{day}.sql"'
copy = f'mkdir ~/backup/{months} && docker cp {container_name}:/var/lib/mysql/{day}.sql ~/backup/{months}'
send = f'cd ~/backup/ && git add ~/backup/{months}/{day}.sql && git commit . -m "Backup from main server ({time.strftime("%Y.%m.%d.%H")})" && git push --set-upstream origin master'
#call(['docker', 'exec', container_name, 'bash', '-c', f'"touch /var/lib/mysql/{day}.sql && mysqldump -u root -p{password} bot > /var/lib/mysql/{day}.sql"'] )
#call(['mkdir', f'~/backup/{months}', '&&', 'docker', 'cp', f'{container_name}:/var/lib/mysql/{day}.sql', f'~/backup/{months}'])
#call(['git', 'commit', '.', '-m', f'"Backup from main server ({time.strftime("%Y.%m.%d.%H")})"', '&&', 'git', 'push'])
os.system(backup)
os.system(copy)
os.system(send)