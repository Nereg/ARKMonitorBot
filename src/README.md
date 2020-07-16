Versioning schema - https://semver.org/
# File descriptions 
* main.py - entire bot entrypoint. Called to start bot
* bot.sql - sql script to init nedded DB tables. Executed by MySql docker image on startup (https://hub.docker.com/_/mysql/ Initializing a fresh instance section)
* config.example.py - example config file MUST be renamed to config.py and edited
* updater.py - entrypoint for second docker-container. Currently used to update DB records. In future will be used also to send notifications.

## Cogs
* server_cmd.py - contains whole !server command with mode selection
* dbl.py - contains DBL(top.gg) code for updating server count on DBL(top.gg)
* commands - contains all other commands like !help , !count and admin commands

## Helpers
* classes.py - contain all custom classes used to encode and transfer data 
* helpers.py - contains some functions like wirk with DB and getting current prefix for commands
* menus.py - contains selection menu 

## Unused files 
* tasks.py - replaced by seperate docker container and update.py. Removed because when task is running (it is big and not async!) bot will not respond to commands
* migration.py - replaced by bot.sql and MySql docker container. Removed because of all problems with finding and running sql script on different platforms 

## Files not in this directory
* dockerfile - dockerfile for bot
* docker-compose.yaml - main docker-conpose file used torun bot with all nedded stuff (like MySql server)
* updater_dockerfile - dockerfile for updater service (see updater.py)
* wait-got-it.sh - shell script used to wait for DB container to start up (https://github.com/vishnubob/wait-for-it) 

## Embeded designes 
* https://bit.ly/3epFi6L - help message