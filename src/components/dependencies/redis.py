import logging
import asyncio

import redis.asyncio as redis
import tanjun

logger = logging.getLogger(__name__)
component = tanjun.Component(name=__name__)

@tanjun.as_loader
def loader(client: tanjun.Client):
    cfg = client.get_type_dependency(dict)
    redis_cfg = cfg["redis"]
    redis_server = redis.Redis(host = redis_cfg['host'])
    client.set_type_dependency(redis.Redis, redis_server)

@tanjun.as_unloader
def unloader(client: tanjun.Client):
    pass