import asyncio
import traceback


class BackgroundTasks:
    def __init__(self, *args, **kwargs):
        self._background_tasks = set()
        super().__init__(*args, **kwargs)

    def start_background_task(self, coro):
        async def log_exceptions():
            try:
                await coro
            except Exception as e:
                traceback.print_exc()

        task = asyncio.create_task(log_exceptions())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
