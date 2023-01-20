import os
import asyncio
import hikari
import tanjun
import config
from db.db import Database
import alluka
import aiohttp
import traceback

# read config
cfg: dict = config.Config().c

def main() -> None:
    # if True slash commands will be declare globally
    declareCommands = True
    # if there is debug guild
    if cfg['debug']['debugGuildId'] != -1:
        # declare slash commands to that guild only
       declareCommands = [cfg['debug']['debugGuildId']] 
    # declare intents for bot
    # TODO: declare less intents
    intents = hikari.Intents.ALL_UNPRIVILEGED
    # create bot object
    bot = hikari.GatewayBot(cfg['discord']['token'], intents=intents)
    # create command handler
    client: tanjun.Client = tanjun.Client.from_gateway_bot(bot, declare_global_commands=declareCommands, mention_prefix=True)
    # loading all components from components directory
    client.load_directory("src/components", namespace="src.components")

    @client.with_client_callback(tanjun.ClientCallbackNames.STARTING)
    async def on_starting(client: alluka.Injected[tanjun.clients.Client]) -> None:
        # create database object
        database: Database = Database(client, cfg)
        try:
            # connect to DB
            await database.connect()
        except Exception as e:
            # if failed print traceback and exit
            print('DB connection failed!')
            print(traceback.format_exc())
            exit(1)
        # injecting config TODO: make it a separate class to not inject std type
        client.set_type_dependency(dict, cfg)
        # inject connected DB instance
        client.set_type_dependency(Database, database)
        # inject http client
        client.set_type_dependency(aiohttp.ClientSession, aiohttp.ClientSession())


    # if we are running not in windows
    if os.name != "nt":
        # import uvloop
        import uvloop
        uvloop.install()
        print('Added uvloop!')
    bot.run()

main()