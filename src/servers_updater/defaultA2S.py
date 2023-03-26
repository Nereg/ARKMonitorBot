import asyncio
import logging
from enum import Enum
from dataclasses import dataclass

import a2s
import asyncpg
import redis.asyncio as redis

import typing

logger = logging.getLogger(__name__)

a2sPlayers = list[a2s.Player]

class ServerVerdict(Enum):
    CRITICAL = -1 # the server isn't ARK one
    OK = 0 # proceed with parsing
    ERROR = 1 # server is offline

@dataclass(slots=True)
class ServerInfo():
    id: int
    info: a2s.SourceInfo | Exception
    players: a2sPlayers | Exception
    rules: dict | Exception

    def __repr__(self) -> str:
        return f'<ServerInfo ID: {self.id}>'

class DefaultA2S():
    
    def __init__(self, db: asyncpg.Pool, redisInst: redis.Redis) -> None:
        self._db = db
        self._redis = redisInst

    async def collect(self, serverList: list[asyncpg.Record]) -> list[ServerInfo]:
        '''
        Gathers info about a range of servers
        '''
        results: list[ServerInfo] = [] # list of results in defined format
        corutines: list[typing.Coroutine] = [] # list of corutines to be .gather'ed
        # for each server in supplied range
        for server in serverList:
            # format it for a2s lib
            ip = tuple(server["ip"].split(":"))
            logger.info(ip)
            # append info and players corutine to be .gather'ed
            corutines.append(a2s.ainfo(ip))
            corutines.append(a2s.aplayers(ip))
            corutines.append(a2s.arules(ip))
        # gather all the generate corutines and n (executes them in parallel)
        info = await asyncio.gather(*corutines, return_exceptions=True)
        logger.info(serverList)
        logger.info(info)
        # form results with dataclasses
        for id, tmpInfo, players, rules in zip([i["id"] for i in serverList], info[::3], info[1::3], info[2::3]):
            results.append(ServerInfo(id, tmpInfo, players, rules))
        logger.info("Results: " + str(results))
        return results

    def evaluateServer(self, server: ServerInfo) -> ServerVerdict:
        # if any exceptions
        if (isinstance(server.info, Exception) or isinstance(server.players, Exception) or isinstance(server.rules, Exception)):
            # TODO: add metrcis on which errors it is
            logger.info(server)
            return ServerVerdict.ERROR
        # check if it is ARK server
        # see https://developer.valvesoftware.com/wiki/Server_queries#Response_Format for EDF 0x01
        try:
            # 346110 is ARK steam id and app_id is 0 because 346110 can't be fit in 16-bit storage
            if (server.info.app_id != 0 or server.info.game_id != 346110):
                return ServerVerdict.CRITICAL
        # info.game_id may not be present
        except AttributeError: 
            return ServerVerdict.CRITICAL
        # if all checks pass return OK
        return ServerVerdict.OK

    async def write(self, serverData: list[ServerInfo]) -> None:
        '''
        Parses and writes info into the DB
        Also responsible for publishing up/down notifications to redis
        '''
        # task of cleaning up servers with more then X ammount of errors is left for the bot
        # SQL query with placeholders for OK results
        okQuery: str = '''UPDATE public.servers
                        SET name = $1, map_name = $2, current_players = $3, max_players = $4,
                        steam_id = $5, ping = $6, password_protected = $7, modded = $8,
                        is_pve = $9, last_updated=TIMESTAMP 'now', online = true, error_count = 0
                        WHERE id = $10;'''
        # SQL query with placeholders for ERROR results
        errorQuery: str = '''UPDATE public.servers
                        SET last_updated=TIMESTAMP 'now', online = false, error_count = error_count + 1
                        WHERE id = $1;'''
        # SQL query with placeholders for CRITICAL results
        criticalQuery: str = '''UPDATE public.servers
                        SET last_updated=TIMESTAMP 'now', online = false, error_count = error_count + 5
                        WHERE id = $1;'''
        # list of sets of parameters for the OK query
        parametersOkQueries: list = []
        # list of sets of parameters for the ERROR query
        parametersErrorQueries: list = []
        # list of sets of parameters for the CRITICAL query
        parametersCriticalQueries: list = []
        # for each collected server
        for server in serverData:
            logger.info(server)
            verdict = self.evaluateServer(server)
            if (verdict == ServerVerdict.OK):
                logger.info(type(server.players))
                # some checks so type checker can shut up
                assert type(server.info) == a2s.SourceInfo
                # IDK why it won't work with a2sPlayers type
                assert type(server.players) == list
                assert type(server.rules) == dict
                # extact some values
                isPVE = bool(server.rules['SESSIONISPVE_i'])
                modded = True if server.rules.get('MOD0_s') is not None else False
                # convert ping to ms
                ping = int(server.info.ping * 1000)
                # constuct a set of arguments to the query
                parametersOkQueries.append((
                    server.info.server_name, server.info.map_name, server.info.player_count,
                    server.info.max_players, server.info.steam_id, ping,
                    server.info.password_protected, modded, isPVE, server.id))
            if (verdict == ServerVerdict.ERROR):
                parametersErrorQueries.append((server.id,))
            if (verdict == ServerVerdict.CRITICAL):
                parametersCriticalQueries.append((server.id,))
        logger.info(parametersOkQueries)
        logger.info(parametersErrorQueries)
        logger.info(parametersCriticalQueries)
        # execute them all
        await asyncio.gather(*[self._db.executemany(okQuery, parametersOkQueries),
                               self._db.executemany(errorQuery, parametersErrorQueries),
                               self._db.executemany(criticalQuery, parametersCriticalQueries)])

    async def refresh(self, serverList: list[asyncpg.Record]) -> None:
        '''
        Gathers info about a list of servers and write the updated info back
        '''
        logger.info(serverList)
        serverData = await self.collect(serverList)
        await self.write(serverData)
