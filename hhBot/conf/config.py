import toml

from types import SimpleNamespace

def dict_to_namespace(d):
    """Recursively converts a dictionary to a SimpleNamespace."""
    if not isinstance(d, dict):
        return d
    return SimpleNamespace(**{k: dict_to_namespace(v) for k, v in d.items()})

def load_config(file_path):
    """Loads a TOML file and returns a SimpleNamespace."""
    config = toml.load(file_path)
    return dict_to_namespace(config)

# config = load_config("./data/custom_setting.toml")
config = toml.load('./data/custom_setting.toml')

HeyChatAPPToken = config['basic']['HeyChatAPPToken']

WSS_URL = config['basic']['WSS_URL']
COMMON_PARAMS = config['basic']['COMMON_PARAMS']
TOKEN_PARAMS = config['basic']['TOKEN_PARAMS']

HTTP_HOST = config['basic']['HTTP_HOST']
SEND_MSG_URL = config['basic']['SEND_MSG_URL']


print(config)
