import asyncio
import os
import traceback
import logging
from logging.handlers import RotatingFileHandler

import aiohttp
import alluka
import hikari
import tanjun

import config
from db.db import Database
from components.metrics import PromMetrics

logger = logging.getLogger(__name__)

def setupLogging() -> None:
    # get root logger
    rootLogger = logging.getLogger("")
    # create a rotating file handler with 1 backup file and 1 megabyte size
    fileHandler = RotatingFileHandler("/logs/bot.log", "w", 1_000_000, 1, "UTF-8")
    # create a default console handler
    consoleHandler = logging.StreamHandler()
    # create a formatting style (modified from hikari)
    formatter = logging.Formatter(
        fmt="%(levelname)-1.1s %(asctime)23.23s %(name)s @ %(lineno)d: %(message)s"
    )
    # add the formatter to both handlers
    consoleHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)
    # add both handlers to the root logger
    rootLogger.addHandler(fileHandler)
    rootLogger.addHandler(consoleHandler)
    # set logging level to info
    rootLogger.setLevel(logging.INFO)

def loadComponents(client: tanjun.Client) -> None:
    # loading all components from components directory
    client.load_directory("./src/components/", namespace="components")
    # load server updater
    client.load_directory("./src/servers_updater")
    logger.info(f"Loaded components: {[c.name for c in client.components]}")

def main() -> None:
    setupLogging()
    # read config
    cfg: dict = config.Config().c

    # if True slash commands will be declare globally
    declareCommands = True
    # if there is debug guild
    if cfg["debug"]["debugGuildId"] != -1:
        # declare slash commands to that guild only
        declareCommands = [cfg["debug"]["debugGuildId"]]
    
    # declare intents for bot
    # TODO: declare less intents
    intents = hikari.Intents.ALL_UNPRIVILEGED
    # create bot object
    bot = hikari.GatewayBot(cfg["discord"]["token"], intents=intents)
    # create command handler
    client: tanjun.Client = tanjun.Client.from_gateway_bot(
        bot, declare_global_commands=declareCommands, mention_prefix=True
    )
    # injecting config TODO: make it a separate class to not inject std type
    client.set_type_dependency(dict, cfg)
    loadComponents(client)

    @client.with_client_callback(tanjun.ClientCallbackNames.STARTING)
    async def on_starting() -> None: 
        # create database object
        database: Database = Database(client, cfg)
        try:
            # connect to DB
            await database.connect()
        except Exception as e:
            # if failed print traceback and exit
            logger.critical("DB connection failed!", exc_info=True)
            #logger.exception(traceback.format_exc())
            exit(1)
        # create metrics server
        metrics: PromMetrics = PromMetrics(bot)
        # inject metrics class
        client.set_type_dependency(PromMetrics, metrics)
        # inject connected DB instance
        client.set_type_dependency(Database, database)
        # inject http client
        client.set_type_dependency(aiohttp.ClientSession, aiohttp.ClientSession())

    # if we are running not in windows
    if os.name != "nt":
        # import uvloop
        import uvloop

        uvloop.install()
        logger.info("Added uvloop!")
    bot.run()


main()
