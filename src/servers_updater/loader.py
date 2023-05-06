import logging
import typing
import asyncio
import time

import tanjun
import alluka
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.asyncio import AsyncIOExecutor
import asyncpg
import redis.asyncio as redis

from servers_updater.defaultA2S import DefaultA2S
from components.dependencies.metrics import PromMetrics

component = tanjun.Component(name=__name__)
logger = logging.getLogger(__name__)


class ServerUpdater:
    def __init__(self, cfg: dict, metrics: PromMetrics, redisInst: redis.Redis) -> None:
        # aps scheluler to be used
        self._scheduler: AsyncIOScheduler
        self._botCfg: dict = cfg
        self._db: asyncpg.Pool
        self._redis: redis.Redis = redisInst
        # list of workers
        self._workers: list[DefaultA2S] = []
        # metrics class to be used
        self._metrics = metrics
        self._setupScheduler()

    async def init(self) -> None:
        # get needed DB config values an constuct connect URL
        user = self._botCfg["db"]["user"]
        host = self._botCfg["db"]["host"]
        db_name = self._botCfg["db"]["dbName"]
        port = self._botCfg["db"]["dbPort"]
        password = self._botCfg["db"]["password"]
        dsn = f"postgres://{user}:{password}@{host}:{port}/{db_name}"
        try:
            # create a pool of connection to the DB
            self._db = await asyncpg.create_pool(dsn=dsn)
        except Exception:
            # if we can't log and exit
            logger.exception("Can't setup DB!", exc_info=True)
            exit(1)
        # create configurable ammount of workers
        for _ in range(0, self._botCfg["updater"]["workers"]):
            # append each to the list of workers
            self._workers.append(DefaultA2S(self._db, self._redis))
        # create main updater task loop
        self._setupUpdaterTask()
        logger.info("Started server updater!")

    def divide(self, n: int, iterable: typing.Iterable):
        """Divide the elements from iterable into n parts, maintaining order.
        Stolen + modified from https://github.com/more-itertools/more-itertools
        """
        if n < 1:
            raise ValueError("n must be at least 1")

        try:
            iterable[:0]
        except TypeError:
            seq = tuple(iterable)
        else:
            seq = iterable

        q, r = divmod(len(seq), n)

        ret = []
        stop = 0
        for i in range(1, n + 1):
            start = stop
            stop += q + 1 if i <= r else q
            ret.append(list(seq[start:stop]))

        return ret

    def _setupUpdaterTask(self) -> None:
        # create a job with single instance which fires in a loop in configurable ammount of seconds
        self._scheduler.add_job(
            self.updateAll,
            "interval",
            seconds=self._botCfg["updater"]["period"],
            max_instances=1,
            replace_existing=True,
        )

    def _setupScheduler(self) -> None:
        # create one and only asyncio executor
        executors = {"default": AsyncIOExecutor()}
        # create scheduler
        scheduler = AsyncIOScheduler(executors=executors)
        # start and assign it to the class
        scheduler.start()
        self._scheduler = scheduler

    async def updateAll(self) -> None:
        """
        Updates all the server found in DB
        """
        logger.info("Started updater task")
        # start performance timer
        startTime = time.perf_counter()
        # get needed info about every server
        servers = await self._db.fetch("SELECT id, ip, online FROM public.servers")
        # set server count metric
        self._metrics.updater_servers_count.set(len(servers))
        # create chunks for every worker
        chunks = self.divide(len(self._workers), servers)
        # DEBUG
        logger.info(chunks)
        # generate corutine for each worker with it's chunk to do
        corutines = []
        for worker, chunk in zip(self._workers, chunks):
            corutines.append(worker.refresh(chunk))
        # run in parallel
        await asyncio.gather(*corutines)
        # end performance timer
        endTime = time.perf_counter()
        # set performance metric
        self._metrics.updater_iteration_timing.set(endTime - startTime)

    @classmethod
    async def build(
        cls, cfg: dict, metrics: PromMetrics, redisInst: redis.Redis
    ) -> typing.Self:
        """Correctly builds the class"""
        inited = cls(cfg, metrics, redisInst)
        await inited.init()
        return inited


@component.with_client_callback(tanjun.ClientCallbackNames.STARTED)
async def start(
    client: alluka.Injected[tanjun.Client],
    cfg: alluka.Injected[dict],
    metrics: alluka.Injected[PromMetrics],
    redisInst: alluka.Injected[redis.Redis],
) -> None:
    updater = await ServerUpdater.build(cfg, metrics, redisInst)
    client.set_type_dependency(ServerUpdater, updater)
    logger.info("Inited and injected server updater!")


loader = component.make_loader()
