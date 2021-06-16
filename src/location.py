import asyncio
import aiohttp
import classes as c
import arrow
import flag

class Location:
    def __init__(self, session) -> None:
        self.session = session
        self.requestsLeft = 45  # https://ip-api.com/docs/api:json
        self.url = 'http://ip-api.com/json/{}?fields=3194883'
        # holds time last request was done (in arrow object)
        self.lastRequestTime = None
        self.waitTime = 0  # holds how many seconds we need to wait
        pass

    async def getEmoji(self, coutryCode: str):
        '''
        coutryCode is in https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2 format
        https://pypi.org/project/emoji-country-flag/
        '''
        return flag.flag(coutryCode)

    async def get(self, ip: str):
        '''
        returns https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2 code of the country IP is in
        if error returns empty string. Rate limited to 45 requests in one minute 
        '''
        #print('Entered function')
        if (self.requestsLeft <= 0):  # if no more requests are allowed
            currentTime = arrow.utcnow()  # get current time
            # calculate how much time passed from last request
            delta = currentTime - self.lastRequestTime
            if (delta.seconds >= 60):  # if more than 60 seconds passed
                self.requestsLeft = 45  # we are good to go
                self.waitTime = 0
            else:  # else
                # if enough time has passed
                if (delta.seconds > self.waitTime):
                    self.requestsLeft = 45  # we are good to go
                    self.waitTime = 0
                else:
                    wait = self.waitTime - delta.seconds  # we need to wait only part of it
                    print(f'Waiting {wait} seconds')
                    await asyncio.sleep(wait)  # sleep
                    self.requestsLeft = 45  # we are good to go
                    self.waitTime = 0

        # format the url and GET it
        try:
            resp = await self.session.get(self.url.format(ip))
            text = await resp.json()  # parse JSON from response
            headers = resp.headers  # extract headers
        # it will throw it with large amount of requests (and somehow slow everything down)
        except aiohttp.client_exceptions.ClientOSError: 
            return ''
        # header X-Rl contains the number of requests remaining in the current rate limit window
        self.requestsLeft = int(headers['X-Rl'])
        self.lastRequestTime = arrow.utcnow()  # get UTC time
        # X-Ttl contains the seconds until the limit is reset.
        self.waitTime = int(headers['X-Ttl'])

        #print(
        #    f'Requests left: {self.requestsLeft}\nWait time: {self.waitTime}')

        if (text['status'] == 'success'):  # request is successful
            return text['countryCode']
        else:
            return ''
