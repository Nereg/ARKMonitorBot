from __future__ import annotations

import asyncio
import logging

import prometheus_client
import psutil
from aiohttp import web
import tanjun
import alluka
import hikari

from components.dependencies.serverCounter import ServerCounter

logger = logging.getLogger(__name__)
component = tanjun.Component(name=__name__).load_from_scope()


class PromMetrics:
    __slots__ = (
        "_site",
        "_registry",
        "_bot",
        "_client",
        "heartbeat_latency",
        "events_received",
        "asyncio_tasks",
        "cpu_usage",
        "ram_usage",
        "guilds",
        "updater_iteration_timing",
        "updater_servers_count",
        "updater_errors",
        "updater_verdicts",
    )

    def __init__(self, client: tanjun.Client) -> None:
        self._site = None
        self._bot = client.get_type_dependency(hikari.GatewayBot)
        self._client = client
        self._registry = prometheus_client.CollectorRegistry()
        self.heartbeat_latency = prometheus_client.Gauge(
            "bot_heartbeat_latency",
            "Bots heartbeat latency",
            unit="ms",
            registry=self._registry,
        )
        self.events_received = prometheus_client.Counter(
            "bot_events_received",
            "Events received",
            labelnames=("name",),
            registry=self._registry,
        )
        self.asyncio_tasks = prometheus_client.Gauge(
            "bot_asyncio_tasks", "Active asyncio tasks", registry=self._registry
        )
        self.cpu_usage = prometheus_client.Gauge(
            "bot_cpu_usage", "CPU usage", registry=self._registry
        )
        self.ram_usage = prometheus_client.Gauge(
            "bot_ram_usage", "RAM usage", registry=self._registry
        )
        self.guilds = prometheus_client.Gauge(
            "bot_guild_count", "Guilds", registry=self._registry
        )
        self.updater_iteration_timing = prometheus_client.Gauge(
            "updater_iteration_timing",
            "Duration of last updater iteration",
            registry=self._registry,
        )
        self.updater_servers_count = prometheus_client.Gauge(
            "updater_servers_count",
            "Ammount of servers updated",
            registry=self._registry,
        )
        self.updater_errors = prometheus_client.Counter(
            "updater_errors",
            "Errors encountered in updater",
            labelnames=("name",),
            registry=self._registry,
        )
        self.updater_verdicts = prometheus_client.Counter(
            "updater_verdicts",
            "Types of verdicts encountered by the updater",
            labelnames=("name",),
            registry=self._registry,
        )
        client.set_type_dependency(PromMetrics, self)

    async def gather_metrics(self) -> str:
        loop = asyncio.get_running_loop()
        server_counter = self._client.get_type_dependency(ServerCounter)
        self.heartbeat_latency.set(self._bot.heartbeat_latency * 1_000)
        self.asyncio_tasks.set(len(asyncio.all_tasks(loop)))
        self.cpu_usage.set(psutil.cpu_percent())
        self.ram_usage.set(psutil.virtual_memory().percent)
        self.guilds.set(server_counter.server_count())
        return prometheus_client.generate_latest(self._registry).decode("utf-8")

    async def serve_metrics(self, _: web.Request) -> web.Response:
        metrics = await self.gather_metrics()

        return web.Response(text=metrics, content_type="text/plain")

    async def start(
        self,
        host: str = "0.0.0.0",
        port: int = 9000,
        disable_access_logger: bool = True,
    ) -> None:
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
async def start_metrics(
    _: hikari.StartedEvent, metrics: alluka.Injected[PromMetrics]
) -> None:
    await metrics.start()


@component.with_listener()
async def stop_metrics_collection(
    _: hikari.StoppingEvent, metrics: alluka.Injected[PromMetrics]
) -> None:
    await metrics.stop()


@component.with_listener()
async def raw_event(
    event: hikari.ShardPayloadEvent, metrics: alluka.Injected[PromMetrics]
) -> None:
    metrics.events_received.labels(name=event.name).inc()


@tanjun.as_loader
def load(client: tanjun.Client):
    PromMetrics(client)
    client.add_component(component)
