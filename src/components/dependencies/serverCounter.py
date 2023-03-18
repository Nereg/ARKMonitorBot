import logging
import typing

import hikari
import tanjun

logger = logging.getLogger(__name__)
component = tanjun.Component(name=__name__)

class ServerCounter():
    '''
    Counts how many discord server the bot is in. Thanks dav!
    '''
    shard_guild_counter: typing.Dict[hikari.Snowflakeish, int] = {}
    
    def __init__(self) -> None:
        pass

    def server_count(self) -> int:
        return sum(self.shard_guild_counter.values())
    
server_counter = ServerCounter()

@component.with_listener()
async def reset_guild_counter(event: hikari.ShardReadyEvent) -> None:
    server_counter.shard_guild_counter[event.shard.id] = len(event.unavailable_guilds)


@component.with_listener()
async def increment_guild_counter(event: hikari.GuildJoinEvent) -> None:
    server_counter.shard_guild_counter[event.shard.id] += 1


@component.with_listener()
async def decrement_guild_counter(event: hikari.GuildLeaveEvent) -> None:
    server_counter.shard_guild_counter[event.shard.id] -= 1

@tanjun.as_loader
def load(client: tanjun.Client):
    client.set_type_dependency(ServerCounter, server_counter)
    client.add_component(component)