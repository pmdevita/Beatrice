from aerich import Command, Migrate
from tortoise import Tortoise
import asyncio


class AerichManager:
    def __init__(self, config, app=None):
        self.config = config
        if app:
            self.app = app
        else:
            self.app = "models"

    async def __aenter__(self):
        self.db_type = self.config.export()["connections"]["default"].split("://")[0]
        self.command = Command(self.config.export(), location=f"./migrations/{self.db_type}", app=self.app)
        return self.command

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await Tortoise.close_connections()


def run_aerich(config, args):
    command = args.aerich
    app = args.app
    func_args = [config]
    if command == "init":
        func = init
    elif command == "init-db":
        func = init_db
    elif command == "migrate":
        func = migrate
        func_args.append(app)
    elif command == "upgrade":
        func = upgrade
        func_args.append(app)
    elif command == "downgrade":
        func = downgrade
        func_args.append(app)
        func_args.append(args.delete)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(func(*func_args))
    loop.close()


async def init_db(config):
    # For some terrible reason, aerich will try to init all of your apps as one migration file
    # So we're only going to let it do itself
    for key in list(config.config["apps"].keys()):
        if key != "aerich":
            config.config["apps"].pop(key)

    async with AerichManager(config, app="aerich") as command:
        try:
            await command.init()
            await command.init_db(True)  # create tables only if they don't exist
        except Exception as e:
            print(e)


async def migrate(config, app=None):
    if app is None:
        apps = config.config["apps"].keys()
    else:
        apps = [app]
    for app in apps:
        async with AerichManager(config, app) as command:
            await command.init()
            # Seems to require this hack ugh
            if Migrate._last_version_content is None:
                Migrate._last_version_content = {}
            Migrate.migrate_location.mkdir(parents=True, exist_ok=True)  # Aerich is legally braindead
            await command.migrate(app)  # create tables only if they don't exist


async def upgrade(config, app=None):
    if app is None:
        apps = config.config["apps"].keys()
    else:
        apps = [app]
    for app in apps:
        async with AerichManager(config, app) as command:
            await command.init()
            await command.upgrade()


async def downgrade(config, app, delete):
    async with AerichManager(config, app) as command:
        await command.init()
        await command.downgrade(-1, delete)


