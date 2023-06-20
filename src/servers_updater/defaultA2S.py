import asyncio
import logging
import typing
from dataclasses import dataclass
from enum import Enum

import a2s
import asyncpg
import redis.asyncio as redis

from components.dependencies.metrics import PromMetrics

logger = logging.getLogger(__name__)

# define players type
a2s_players = list[a2s.Player]


class ServerVerdict(Enum):
    CRITICAL = -1  # the server isn't ARK one
    "Reserved for critical cases, like if a server isn't ARK one"
    OK = 0  # proceed with parsing
    "Server is working correctly"
    ERROR = 1  # server is offline
    "Server is offline or misbehaving"
    PARTIAL = 2  # some data isn't present
    "Server returned partial data"


@dataclass(slots=True)
class ServerInfo:
    """
    Internal representation of info fetched from a server
    """

    id: int
    "Server ID in the DB"
    info: a2s.SourceInfo | Exception
    "SourceInfo class about the server or exception"
    players: a2s_players | Exception
    "A list of Player objects or exception"
    rules: dict | Exception
    "A dict of rules on the server or exception"
    last_online: bool
    "Last online value in the DB"

    def __repr__(self) -> str:
        return f"<ServerInfo ID: {self.id} {type(self.info)} {type(self.players)} {type(self.rules)}>"


class DefaultA2S:
    """
    Default implementation of server updater
    """

    def __init__(
        self, db: asyncpg.Pool, redis_inst: redis.Redis, metrics: PromMetrics
    ) -> None:
        self._db = db
        """Instance of the DB"""
        self._redis = redis_inst
        """Instance of redis"""
        self._redis_executor = redis_inst.pipeline()
        """A redis pipeline for buffering many changes"""
        self._channel_name = "server_watch"
        """Name of a redis channel for server notifications"""
        self._timeout = 6.0
        """Timeout for server requests"""
        self._metrics = metrics
        """Metrics class to write to"""

    async def collect(self, server_list: list[asyncpg.Record]) -> list[ServerInfo]:
        """
        Gathers info about a range of servers
        """
        results: list[ServerInfo] = []  # list of results in defined format
        corutines: list[typing.Coroutine] = []  # list of corutines to be .gather'ed
        # for each server in supplied range
        for server in server_list:
            # format it for a2s lib
            ip = tuple(server["ip"].split(":"))
            # logger.info(ip)
            # append info and players corutine to be .gather'ed
            corutines.append(a2s.ainfo(ip, timeout=self._timeout))
            corutines.append(a2s.aplayers(ip, timeout=self._timeout))
            corutines.append(a2s.arules(ip, timeout=self._timeout))
        # gather all the generated corutines (executes them in parallel)
        # any exceptions will be placed as results
        info = await asyncio.gather(*corutines, return_exceptions=True)
        # logger.info(serverList)
        # logger.info(info)
        # form results with dataclasses
        for id, tmp_info, tmp_players, tmp_rules, last_online in zip(
            [i["id"] for i in server_list],
            info[::3],  # info
            info[1::3],  # players
            info[2::3],  # rules
            [i["online"] for i in server_list],
        ):
            results.append(
                ServerInfo(id, tmp_info, tmp_players, tmp_rules, last_online)
            )
        # logger.info("Results: " + str(results))
        return results

    def evaluateServer(self, server: ServerInfo) -> ServerVerdict:
        """
        Judges which case we have with a server
        OK - all data is present and is from ARK server
        PARTIAL - some data isn't present, no checks should be performed
        ERROR - no data is present, server is down
        CRITICAL - the server probably isn't an ARK one, or other critical errors
        """
        # if all exceptions
        if (
            isinstance(server.info, Exception)
            and isinstance(server.players, Exception)
            and isinstance(server.rules, Exception)
        ):
            # TODO: add metrcis on which errors it is
            logger.info("all exceptions: " + str(server))
            return ServerVerdict.ERROR

        # if any exceptions
        if (
            isinstance(server.info, Exception)
            or isinstance(server.players, Exception)
            or isinstance(server.rules, Exception)
        ):
            # TODO: add metrcis on which errors it is
            logger.info("some exceptions: " + str(server))
            return ServerVerdict.PARTIAL

        # check if it is ARK server
        # see https://developer.valvesoftware.com/wiki/Server_queries#Response_Format for EDF 0x01
        try:
            # 346110 is ARK steam id and app_id is 0 because 346110 can't be fit in 16-bit storage
            if server.info.app_id != 0 or server.info.game_id != 346110:
                logger.info(f"CRITICAL {server} {server.info.game_id}")
                return ServerVerdict.CRITICAL
        # info.game_id may not be present
        except AttributeError:
            logger.info(f"CRITICAL {server}")
            return ServerVerdict.CRITICAL

        # if all checks pass return OK
        return ServerVerdict.OK

    def declare_up(self, up_array: list[int]) -> None:
        """
        Declares all IDs in up_array as up in proper redis channel
        """
        for id in up_array:
            logger.info(f"UP: {id}")
            self._redis_executor.publish(self._channel_name, "UP;" + str(id))

    def declare_down(self, down_array: list[int]) -> None:
        """
        Declares all IDs in down_array as down in proper redis channel
        """
        for id in down_array:
            logger.info(f"DOWN: {id}")
            self._redis_executor.publish(self._channel_name, "DOWN;" + str(id))

    def exception_metrics_write(
        self, verdict: ServerVerdict, server: ServerInfo
    ) -> None:
        # maybe add a way to know which of the requests failed?
        if isinstance(server.info, Exception):
            self._metrics.updater_errors.labels(name=str(type(server.info))).inc()
        if isinstance(server.players, Exception):
            self._metrics.updater_errors.labels(name=str(type(server.players))).inc()
        if isinstance(server.rules, Exception):
            self._metrics.updater_errors.labels(name=str(type(server.rules))).inc()
        # add the name of the verdict to our metrics
        self._metrics.updater_verdicts.labels(name=verdict.name.lower()).inc()

    async def write(self, server_data: list[ServerInfo]) -> None:
        """
        Parses and writes info into the DB
        Responsible for publishing up/down notifications to redis
        The task of cleaning up servers with more then X amount of errors is left for the bot
        """
        # SQL query with placeholders for OK results
        ok_query: str = """UPDATE public.servers
                        SET name = $1, map_name = $2, current_players = $3, max_players = $4,
                        steam_id = $5, ping = $6, password_protected = $7, modded = $8,
                        is_pve = $9, last_updated=TIMESTAMP 'now', online = true, error_count = 0
                        WHERE id = $10;"""
        # SQL query with placeholders for PARTIAL results
        partial_query: str = """UPDATE public.servers
                        SET last_updated=TIMESTAMP 'now', online = true
                        WHERE id = $1;"""
        # SQL query with placeholders for ERROR results
        error_query: str = """UPDATE public.servers
                        SET last_updated=TIMESTAMP 'now', online = false, error_count = error_count + 1
                        WHERE id = $1;"""
        # SQL query with placeholders for CRITICAL results
        critical_query: str = """UPDATE public.servers
                        SET last_updated=TIMESTAMP 'now', online = false, error_count = error_count + 10
                        WHERE id = $1;"""
        # SQL query to delete player list for a server from DB
        players_delete_query: str = "DELETE FROM public.players WHERE server_id = $1;"
        # SQL query to add player list for a server to DB
        players_add_query: str = """INSERT INTO public.players (server_id, name, duration)
                                    VALUES ($1, $2, $3);"""

        # list of sets of parameters for the OK query
        parameters_ok_oueries: list = []
        # list of sets of parameters for the ERROR query
        parameters_error_queries: list = []
        # list of sets of parameters for the CRITICAL query
        parameters_critical_queries: list = []
        # list of sets of parameters for the PARTIAL query
        parameters_partial_queries: list = []
        # array of ids of servers that went down
        went_down: list[int] = []
        # array of ids of servers that went up
        went_up: list[int] = []
        # array of parameters for player info
        players: list[tuple[int, str, float]] = []

        # for each collected server
        for server in server_data:
            # logger.info(server)
            # judge the server result
            verdict = self.evaluateServer(server)
            # record the metrics
            self.exception_metrics_write(verdict, server)
            # if full data is present
            if verdict == ServerVerdict.OK:
                # some checks so type checker can shut up
                assert type(server.info) == a2s.SourceInfo
                # IDK why it won't work with a2sPlayers type
                assert type(server.players) == list
                assert type(server.rules) == dict
                # extact some values
                isPVE = bool(server.rules["SESSIONISPVE_i"])
                # if there is a mod then the server is modded
                modded = True if server.rules.get("MOD0_s") is not None else False
                # convert ping to ms
                ping = int(server.info.ping * 1000)
                # constuct a set of arguments to the OK query
                parameters_ok_oueries.append(
                    (
                        server.info.server_name,
                        server.info.map_name,
                        server.info.player_count,
                        server.info.max_players,
                        server.info.steam_id,
                        ping,
                        server.info.password_protected,
                        modded,
                        isPVE,
                        server.id,
                    )
                )
                # for each player on the server
                for player in server.players:
                    # skip blank players. Probably Epic Games players
                    if player.name == "":
                        continue
                    # construct a set of arguments to the player data query
                    players.append((server.id, player.name, player.duration))
                # logger.info("server.last_online: " + str(server.last_online))
                # if server was offline
                if server.last_online == False:
                    # add it to went up list
                    went_up.append(server.id)
                    logger.info(str(server.id) + " went up!")
            # if server returned partial data
            elif verdict == ServerVerdict.PARTIAL:
                # DEBUG
                self._redis_executor.publish("server_watch", "part")
                # write to DB
                parameters_partial_queries.append((server.id,))
                # if needed notify that it went up
                # don't count partial data as went down
                if server.last_online == False:
                    # add it to went up list
                    went_up.append(server.id)
            # if server is fully offline
            elif verdict == ServerVerdict.ERROR:
                # write to DB
                parameters_error_queries.append((server.id,))
                # if server was online
                if server.last_online == True:
                    # add it to went down list
                    went_down.append(server.id)
                    logger.info(
                        str(server.id)
                        + " went down "
                        + str([server.info, server.players, server.rules])
                    )
            # if the server isn't ARK server or other critical error
            elif verdict == ServerVerdict.CRITICAL:
                # write to DB
                parameters_critical_queries.append((server.id,))
                # if server was online
                if server.last_online == True:
                    # add it to went down list
                    went_down.append(server.id)
                    logger.info(
                        str(server.id)
                        + " went down! "
                        + str([server.info, server.players, server.rules])
                    )
        # logger.info(parametersOkQueries)
        logger.info(f"Error parameters: {parameters_error_queries}")
        logger.info(f"Critical parameters: {parameters_critical_queries}")
        logger.info(f"Partial parameters: {parameters_partial_queries}")

        # execute every IO operation
        # half or more servers went down (then they will get up)
        # it is probably a problem on our side
        if (
            len(went_down) >= len(server_data) / 2
            or len(went_down) >= len(server_data) / 2
        ):
            logger.warning(
                "More then half of the servers went down/up in one go! Applying special case."
            )
            # process only OK servers
            await self._db.executemany(ok_query, parameters_ok_oueries)
        # standard case
        else:
            # proccess notifications
            self.declare_up(went_up)
            self.declare_down(went_down)
            # process server info and notifications in parallel
            await asyncio.gather(
                *[
                    self._db.executemany(ok_query, parameters_ok_oueries),
                    self._db.executemany(error_query, parameters_error_queries),
                    self._db.executemany(critical_query, parameters_critical_queries),
                    self._db.executemany(partial_query, parameters_partial_queries),
                    self._redis_executor.execute(),
                ]
            )
            # handling player data
            # construct parameters for delete query (converted to set to de-dupe the ids)
            delete_parameters = list(set([(p[0],) for p in players]))
            # acquire a DB connection
            async with self._db.acquire() as con:
                # open a transaction for player info (I don't want player data to disappear)
                async with con.transaction():
                    # delete player lists
                    await con.executemany(players_delete_query, delete_parameters)
                    # add new onces
                    await con.executemany(players_add_query, players)
            # a query for future me)
            # SELECT server_id, servers.name, servers.ip, servers.current_players, players.name, duration FROM public.players
            # INNER JOIN public.servers
            # ON servers.id = players.server_id
            # WHERE server_id = 10

    async def refresh(self, server_list: list[asyncpg.Record]) -> None:
        """
        Gathers info about a list of servers and write the updated info back
        """
        # logger.info(server_list)
        server_data = await self.collect(server_list)
        await self.write(server_data)
