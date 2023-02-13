from __future__ import annotations

import asyncio
import logging
import random
import typing

import prometheus_client
import psutil
from aiohttp import web
import tanjun
import alluka
import hikari

logger = logging.getLogger(__name__)
component = tanjun.Component(name=__name__)

class PromMetrics:
    __slots__ = (
        "_site",
        "_registry",
        "_bot",
        "heartbeat_latency",
        "events_received",
        "asyncio_tasks",
        "cpu_usage",
        "ram_usage",
        "guilds",
    )

    def __init__(self, bot: hikari.GatewayBot) -> None:
        self._site = None
        self._bot = bot
        self._registry = prometheus_client.CollectorRegistry()

        self.heartbeat_latency = prometheus_client.Gauge(
            "bot_heartbeat_latency", "Bots heartbeat latency", unit="ms", registry=self._registry
        )
        self.events_received = prometheus_client.Counter(
            "bot_events_received", "Events received", labelnames=("name",), registry=self._registry
        )
        self.asyncio_tasks = prometheus_client.Gauge(
            "bot_asyncio_tasks", "Active asyncio tasks", registry=self._registry
        )
        self.cpu_usage = prometheus_client.Gauge("bot_cpu_usage", "CPU usage", registry=self._registry)
        self.ram_usage = prometheus_client.Gauge("bot_ram_usage", "RAM usage", registry=self._registry)
        self.guilds = prometheus_client.Gauge("bot_guild_count", "Guilds", registry=self._registry)

    async def gather_metrics(self) -> str:
        loop = asyncio.get_running_loop()
        self.heartbeat_latency.set(self._bot.heartbeat_latency * 1_000)
        self.asyncio_tasks.set(len(asyncio.all_tasks(loop)))
        self.cpu_usage.set(psutil.cpu_percent())
        self.ram_usage.set(psutil.virtual_memory().percent)
        self.guilds.set(await self._bot.rest.fetch_my_guilds().count())
        return prometheus_client.generate_latest(self._registry).decode("utf-8")

    async def serve_metrics(self, _: web.Request) -> web.Response:
        metrics = await self.gather_metrics()

        return web.Response(text=metrics, content_type="text/plain")

    async def start(self, host: str = "0.0.0.0", port: int = 9000, disable_access_logger: bool = True) -> None:
        if disable_access_logger:
            access_logger = logging.getLogger("aiohttp.access")
            access_logger.disabled = True

        metrics_app = web.Application()
        metrics_app.add_routes((web.get("/metrics", self.serve_metrics),))

        runner = web.AppRunner(metrics_app)
        await runner.setup()

        self._site = web.TCPSite(runner, host=host, port=port)
        await self._site.start()
        logger.info(f"Started metrics server on {host}:{port}!")

    async def stop(self) -> None:
        await self._site.stop()

@component.with_listener()
async def start_metrics(_: hikari.StartedEvent, metrics: alluka.Injected[PromMetrics]) -> None:
    await metrics.start()


@component.with_listener()
async def stop_metrics_collection(_: hikari.StoppingEvent, metrics: alluka.Injected[PromMetrics]) -> None:
    await metrics.stop()


@component.with_listener()
async def raw_event(event: hikari.ShardPayloadEvent, metrics: alluka.Injected[PromMetrics]) -> None:
    metrics.events_received.labels(name=event.name).inc()

loader = component.make_loader()