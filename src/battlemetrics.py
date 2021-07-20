import aiohttp 
import asyncio
import aiomysql
import json 
import arrow 

class BattlemetricsPlugin():

    def __init__(self,updater) -> None:
        print('Initing battlemetrics plugin!')
        # if true than the plugin will modify the record
        # for DB so all mutable plugins will be ran one-by-one and not concurrently
        # (cuz I don't want to mess with syncing of all changes)
        self.mutable = True         
        # main updater class 
        self.updater = updater
        # http pool for APIs
        self.httpPool = self.updater.httpSession
        # sql pool 
        self.sqlPool = self.updater.sqlPool
        # api url
        self.apiURL = 'https://api.battlemetrics.com/servers?fields[server]=name,ip,portQuery&filter[game]=ark&filter[search]={}'
        # battle url
        self.battleURL = 'https://www.battlemetrics.com/servers/ark/{}'
        # time in seconds to wait before ratelimit is lifted
        self.ratelimitWait = 60

    # will be ran by main updater just like regular __init__
    async def init(self):
        pass

    # checks if ratelimit is lifted
    # false if ratelimit is lifted
    # true if ratelimit isn't lifted
    def ratelimitCheck(self):
        # if we have the attribute
        if (hasattr(self,'ratelimitStart')):
            # get current time
            currentTime = arrow.utcnow()
            # calculate difference 
            diff = currentTime - self.ratelimitStart
            # if we waited long enough
            if (diff.seconds >= self.ratelimitWait):
                # return false
                return False
            else:
                # else return true
                return True
        # if we don't have the attribute
        else:
            # return false
            return False


    # updateResults - main array from updater to modify
    # serversToUpdate - array of positions in updateResults which we need to update
    async def getUrls(self, updateResults, serversToUpdate):
        # check if we need to update anything
        if (serversToUpdate.__len__() <= 0):
            # if not just return main array as is
            return updateResults
        # check if we are ratelimited
        if (self.ratelimitCheck()):
            # if we are ratelimited
            # just return everything as is 
            # (we'll get to them later)
            return updateResults
        # for each server we need to update
        for i in serversToUpdate:
            # get current server record
            currentServerRecord = updateResults[i]
            # get current server
            currentServer = currentServerRecord.cachedServer
            # construct API url
            url = self.apiURL.format(currentServer.name)
            # call API (not in batches to not trigger ratelimit)
            result = await self.httpPool.get(url)
            # if request is successful
            if (result.status == 200):
                # decode JSON from response
                data = await result.json()
                # get main data 
                data = data['data']
                # get data of needed server
                ip = currentServer.address
                queryPort = currentServer.port
                # for each server 
                for server in data:
                    # if we found needed server
                    if (server['attributes']['ip'] == ip and int(server['attributes']['portQuery']) == queryPort):
                        # get it's id
                        battleId = int(server['id'])
                        # make it's url 
                        battleUrl = self.battleURL.format(battleId)
                        # record the url and id to DB
                        updateResults[i].moreInfo['battleUrl'] = battleUrl
                        updateResults[i].moreInfo['battleId'] = battleId
                        # break the loop 
                        break
            # if request is ratelimited
            elif (result.status == 429):
                # record current time
                self.ratelimitStart = arrow.utcnow()
                # do not update rest
                return updateResults
            else:
                pass
        return updateResults

    # will handle a batch of server updates
    # must return same sized array of update results
    async def handle(self,updateResults):
        # list for servers we don't have URL for 
        emptyServers = []
        # for each server
        for i,result in enumerate(updateResults):
            # if we already have URL in DB
            if ("battleUrl" in result.moreInfo and "battleId" in result.moreInfo):
                # we don't need to do anything
                continue
            # if we have url in old place
            elif (hasattr(result.cachedServer,'battleURL')):
                # get the url
                url = result.cachedServer.battleURL
                # get components of the url
                # >>> url.split('/') 
                # ['https:', '', 'www.battlemetrics.com', 'servers', 'ark', '7308683']
                components = url.split('/')
                # last component will be the server id
                Id = components[-1]
                # add new keys to old record
                updateResults[i].moreInfo['battleUrl'] = url
                updateResults[i].moreInfo['battleId'] = Id
                # continue
                continue
            # if server is offline
            elif (result.serverRecord[7] == 0):
                # don't update it
                continue
            else:
                # we need to get info and add it to the DB
                emptyServers.append(i)
        # update servers which don't contain URL and id anywhere
        updateResults = await self.getUrls(updateResults, emptyServers)
        # return results
        return updateResults