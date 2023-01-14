import os
import asyncio
import hikari
import tanjun
import config

# read config
cfg: dict = config.Config().c

def main() -> None:
    # if True slash commands will be declare globally
    declareCommands = True
    # if there is debug guild
    if cfg['debug']['debugGuildId'] != -1:
        # declare slash commands to that guild only
       declareCommands = [cfg['debug']['debugGuildId']] 
    # declare intents for bot
    # TODO: declare less intents
    intents = hikari.Intents.ALL_UNPRIVILEGED
    # create bot object
    bot = hikari.GatewayBot(cfg['discord']['token'], intents=intents)
    # create command handler
    client = tanjun.Client.from_gateway_bot(bot, declare_global_commands=declareCommands, mention_prefix=True)
    # loading all components from components directory
    client.load_directory("components", namespace="components")
    
    # if we are running not in windows
    if os.name != "nt":
        # import uvloop
        import uvloop
        uvloop.install()
        print('Added uvloop!')
    bot.run()

main()