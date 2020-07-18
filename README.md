# First open-source discord bot for monitoring ARK servers!
## You can install by doing this
* `git clone https://github.com/Nereg/ARKMonitorBot.git` - clone this repository
* `cd ./ARKMonitorBot/src` - go into bot's settings
* `nano config.example.py` - open default config file 
* `mv config.example.py config.py` - rename default config 
* `cd ..` - go to main bot's directory
* `sudo docker-compose up -d --build` - start bot (you can lear how to install dokcer and docker-compose [here](https://calendarific.com/blog/how-to-install-docker-and-docker-compose-on-ubuntu-20-04-lts-focal-fossa))

## Usefull links
* https://github.com/Yepoleb/python-a2s/ - library I am using to get info about ARK servers (MIT License Copyright (c) 2020 Gabriel Huber)
* https://github.com/Yepoleb/python-a2s/issues/11 - if server cannot be added to bot because it is offline but in reality it is online
* https://github.com/Yepoleb/python-a2s/issues/9 - async version of library I am using to get inforation about ARK servers
* https://ark.gamepedia.com/Web_API - how I get current ARK version
* https://ark.gamepedia.com/Server_Browser - how I get additional info about ARK servers 
* https://discord.gg/NxEVYBt - our discord support server
* олег#3220 - I am on discord

## Contributing
Just open PR I will test it and merge !

# Repository uses license [GNU GPLv3](/LICENSE) 
