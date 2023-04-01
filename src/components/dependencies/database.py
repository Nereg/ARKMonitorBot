import asyncio
import logging

import tanjun

from db.db import Database

logger = logging.getLogger(__name__)
component = tanjun.Component(name=__name__)


@tanjun.as_loader
def load(client: tanjun.Client):
    cfg = client.get_type_dependency(dict)
    # create database object
    database: Database = Database(client, cfg)
    try:
        # connect to DB
        asyncio.run(database.connect())
    except Exception as e:
        # if failed print traceback and exit
        logger.critical("DB connection failed!", exc_info=True)
        exit(1)
    # inject connected DB instance
    client.set_type_dependency(Database, database)
    client.add_component(component)
