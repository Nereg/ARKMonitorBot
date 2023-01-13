import tomllib # import native TOML reader

# path to config
CONFIG_PATH = './config.toml'

class Config():
    def __init__(self) -> None:
        '''
        Reads config TOML file and places it in property c

        Returns
        -------

        none
        '''
        with open(CONFIG_PATH, 'r') as f:
            _cfg_str: str = f.read()
            self.c: dict = tomllib.loads(_cfg_str)
