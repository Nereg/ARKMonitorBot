import asyncio
import logging

import a2s
import asyncpg

import typing

logger = logging.getLogger(__name__)

a2sPlayers = list[a2s.Player]
serverInfo = typing.Tuple[int, a2s.SourceInfo, a2sPlayers, dict]

class DefaultA2S():
    
    def __init__(self, db: asyncpg.Pool) -> None:
        self._db = db

    async def collect(self, serverList: list[asyncpg.Record]) -> list[serverInfo]:
        '''
        Gathers info about a range of servers
        '''
        results: list[serverInfo] = [] # list of results in defined format
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
        # form results with each element: [id, ainfo_result, aplayers_result, arules_result]
        results = list(zip([i["id"] for i in serverList], info[::3], info[1::3], info[2::3]))
        logger.info("Results: " + str(results))
        return results

    async def write(self, serverData: list[serverInfo]) -> None:
        '''
        Parses and write info into the DB
        '''
        # SQL query with placeholders for values
        query: str = '''UPDATE public.servers
                        SET name = $1, map_name = $2, current_players = $3, max_players = $4,
                        steam_id = $5, ping = $6, password_protected = $7, modded = $8,
                        is_pve = $9, last_updated=TIMESTAMP 'now'
                        WHERE id = $10;'''
        # list of sets of parameters for the query
        parametersServers: list = []
        # for each collected server
        for server in serverData:
            logger.info(server)
            # make shortcuts
            info: a2s.SourceInfo = server[1]
            players: a2sPlayers = server[2]
            rules: dict = server[3]
            # TODO: check if it is ARK server, check what caused the exception
            if (isinstance(info, Exception) or isinstance(players, Exception) or isinstance(rules, Exception)):
                logger.warning("Exception with server id: " + str(server[0]))
                continue # TODO: error handling (queues ?)
            # extact some values
            isPVE = bool(rules['SESSIONISPVE_i'])
            modded = True if rules.get('MOD0_s') is not None else False
            # convert ping to ms
            ping = int(info.ping * 1000)
            # constuct a set of arguments to the query
            parametersServers.append((
                info.server_name, info.map_name, info.player_count,
                info.max_players, info.steam_id, ping,
                info.password_protected, modded, isPVE, server[0]))
        logger.info(parametersServers)
        # execute them all
        await self._db.executemany(query, parametersServers)

    async def refresh(self, serverList: list[asyncpg.Record]) -> None:
        '''
        Gathers info about a list of servers and write the updated info back
        '''
        logger.info(serverList)
        serverData = await self.collect(serverList)
        await self.write(serverData)
