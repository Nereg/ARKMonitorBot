import os
import asyncio
import hikari
import tanjun
import config

# read 
cfg = config.Config().c

def main():
    # create bot object
    bot = hikari.GatewayBot(token=cfg['discord']['token'], intents=hikari.Intents.ALL_UNPRIVILEGED)
    # if we are running not in windows
    if os.name != "nt":
        # import uvloop
        import uvloop
        uvloop.install()
        print('Added uvloop!')
    bot.run()

main()