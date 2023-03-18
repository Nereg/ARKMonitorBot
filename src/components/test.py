import logging

import tanjun
import alluka
import hikari
import redis.asyncio as redis

from components.dependencies.serverCounter import ServerCounter

component = tanjun.Component(name=__name__)
logger = logging.getLogger(__name__)

@component.with_command
@tanjun.with_int_slash_option('test', 'testing option')
@tanjun.as_slash_command("name", "description")
async def slash_command(ctx: tanjun.abc.SlashContext, test: int, cfg: alluka.Injected[dict], counter: alluka.Injected[ServerCounter], redis: alluka.Injected[redis.Redis]) -> None:
    queue = redis.pubsub()
    await queue.subscribe('testchannel')
    await redis.publish('testchannel', 'testdata')
    await ctx.respond(f"Ping successful: {queue.channels}, {[await queue.get_message() for _ in range(0,10)]}")
    logger.info('Ran test command!')

loader = component.make_loader()