BASE_CONFIG = {
    "connections": {},
    "apps": {
        "aerich": {
            "models": ["aerich.models"],
            "default_connection": "default",
        },
    },
}


class TortoiseConfig:
    def __init__(self):
        self.config = BASE_CONFIG

    def add_connection(self, url, name="default"):
        self.config["connections"][name] = url

    def add_models(self, name, model_module):
        self.config["apps"][name] = {"models": [model_module], "default_connection": "default"}

    def export(self):
        return self.config


