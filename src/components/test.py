import logging

import alluka
import hikari
import redis.asyncio as redis
import tanjun
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from components.dependencies.serverCounter import ServerCounter

component = tanjun.Component(name=__name__)
logger = logging.getLogger(__name__)


async def debug_redis_handler(queue, ctx: tanjun.abc.SlashContext) -> None:
    msgs = [
        await queue.get_message(ignore_subscribe_messages=True) for _ in range(0, 10)
    ]
    await ctx.respond(msgs)


@component.with_command
@tanjun.with_int_slash_option("test", "testing option")
@tanjun.as_slash_command("name", "description")
async def slash_command(
    ctx: tanjun.abc.SlashContext,
    test: int,
    cfg: alluka.Injected[dict],
    counter: alluka.Injected[ServerCounter],
    redis: alluka.Injected[redis.Redis],
    scheduler: alluka.Injected[AsyncIOScheduler],
) -> None:
    queue = redis.pubsub()
    await queue.subscribe("server_watch")
    scheduler.add_job(
        debug_redis_handler,
        "interval",
        args=[queue, ctx],
        seconds=20,
        max_instances=1,
    )
    await ctx.respond(
        f"Ping successful: {queue.channels}, {[await queue.get_message(ignore_subscribe_messages=True) for _ in range(0,10)]}"
    )
    logger.info("Ran test command!")


loader = component.make_loader()
