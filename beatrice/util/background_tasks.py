import asyncio


class BackgroundTasks:
    def __init__(self, *args, **kwargs):
        self._background_tasks = set()
        super().__init__(*args, **kwargs)

    def start_background_task(self, coro):
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
