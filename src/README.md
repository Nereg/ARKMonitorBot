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
https://discohook.org/?message=eyJtZXNzYWdlIjp7ImVtYmVkcyI6W3sidGl0bGUiOiJJbmZvIGFib3V0IHtib3RzX25hbWV9IiwiZmllbGRzIjpbeyJuYW1lIjoiSW52aXRlIGxpbmsiLCJ2YWx1ZSI6IltIZXJlIV0oaHR0cHM6Ly9iaXQubHkvQVJLVG9wKSIsImlubGluZSI6dHJ1ZX0seyJuYW1lIjoiR2l0SHViIiwidmFsdWUiOiJbSGVyZSFdKGh0dHBzOi8vZ2l0aHViLmNvbS9OZXJlZy9BUktNb25pdG9yQm90KSIsImlubGluZSI6dHJ1ZX0seyJuYW1lIjoiU3VwcG9ydCBzZXJ2ZXIiLCJ2YWx1ZSI6IltIZXJlIV0oaHR0cHM6Ly9kaXNjb3JkLmdnL1FiU0RIdHEpIiwiaW5saW5lIjp0cnVlfSx7Im5hbWUiOiJTZXJ2ZXJzIGluIGRhdGFiYXNlIiwidmFsdWUiOiIxMCIsImlubGluZSI6dHJ1ZX0seyJuYW1lIjoiUkFNIiwidmFsdWUiOiIxLjVHLzIuNUciLCJpbmxpbmUiOnRydWV9LHsibmFtZSI6IkNvbW1pdCIsInZhbHVlIjoiW2AxMjM0NTZgXShodHRwczovL2dpdGh1Yi5jb20vTmVyZWcvQVJLTW9uaXRvckJvdC9jb21taXQvYzZjOGZhNTliYzA1MmRiMjViMzg0ZDc5MTExZDg3OGM2NTdiZDIwNykiLCJpbmxpbmUiOnRydWV9LHsibmFtZSI6IlBpbmciLCJ2YWx1ZSI6IjEwMCBtcyIsImlubGluZSI6dHJ1ZX0seyJuYW1lIjoiQ3JlYXRvciIsInZhbHVlIjoidGVzdCMxMjM0IiwiaW5saW5lIjp0cnVlfSx7Im5hbWUiOiJDdXJyZW50bHkgaW4iLCJ2YWx1ZSI6IjI0IHNlcnZlcnMiLCJpbmxpbmUiOnRydWV9LHsibmFtZSI6IlJvbGUgb24gdGhpcyBzZXJ2ZXIiLCJ2YWx1ZSI6IkB0ZXN0IiwiaW5saW5lIjp0cnVlfSx7Im5hbWUiOiJDdXJyZW50IHByZWZpeCIsInZhbHVlIjoiISIsImlubGluZSI6dHJ1ZX0seyJuYW1lIjoiQ1BVIHV0aWxpc2F0aW9uICIsInZhbHVlIjoiMyAlIiwiaW5saW5lIjp0cnVlfV0sImZvb3RlciI6eyJ0ZXh0IjoiQm90IHYwLjEg4oCiIEdQTHYzIOKAoiBSZXF1ZXN0ZWQgYnkge25hbWV9In0sInRpbWVzdGFtcCI6IjIwMjAtMDgtMDFUMjE6MDA6MDAuMDAwWiJ9XX19