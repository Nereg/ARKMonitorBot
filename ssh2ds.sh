#!/usr/bin/env bash
#based on https://github.com/pdacity/ssh2tg
#script that sends message to discord webhook when someone (hopefully only me) logs in ssh 
#SETUP:
#Move this file to /usr/local/bin/ssh2ds.sh
#Add to /etc/pam.d/sshd :
#session optional pam_exec.so type=open_session seteuid /usr/local/bin/ssh2ds.sh
URL="https://discordapp.com/api/webhooks/************/********************" #your webhook url
DATE1="$(date "+%H:%M:%S")"
DATE2="$(date "+%d %B %Y")"
GEO="$(curl ipinfo.io/$PAM_RHOST)"
TEXT="**$PAM_USER** loged into **$HOSTNAME** 
Time: $DATE1
Date: $DATE2
IP: $PAM_RHOST
Service: $PAM_SERVICE
TTY: $PAM_TTY
GEO: ${GEO}"
curl -X POST -s --max-time 10 --retry 5 --retry-delay 2 --retry-max-time 10 -F "content=$TEXT" $URL > /dev/null 2>&1 &
#curl -s --max-time 10 --retry 5 --retry-delay 2 --retry-max-time 10 -d "$PAYLOAD" $URL > /dev/null 2>&1 &