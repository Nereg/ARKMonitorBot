import logging

import tanjun
import alluka
import hikari

from components.dependencies.serverCounter import ServerCounter

component = tanjun.Component(name=__name__)
logger = logging.getLogger(__name__)

@component.with_command
@tanjun.with_int_slash_option('test', 'testing option')
@tanjun.as_slash_command("name", "description")
async def slash_command(ctx: tanjun.abc.SlashContext, test: int, cfg: alluka.Injected[dict], counter: alluka.Injected[ServerCounter]) -> None:

    await ctx.respond(counter)
    logger.info('Ran test command!')

loader = component.make_loader()