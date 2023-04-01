import logging

import alluka
import tanjun
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)
component = tanjun.Component(name=__name__)


@component.with_client_callback(tanjun.ClientCallbackNames.STARTED)
async def start(
    client: alluka.Injected[tanjun.Client],
):
    # create one and only asyncio executor
    executors = {"default": AsyncIOExecutor()}
    # create and start scheduler
    scheduler = AsyncIOScheduler(executors=executors)
    scheduler.start()
    # inject scheduler
    client.set_type_dependency(AsyncIOScheduler, scheduler)


@tanjun.as_loader
def load(client: tanjun.Client):
    client.add_component(component)
