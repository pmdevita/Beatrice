import asyncio

# What are tasks for? https://stackoverflow.com/questions/57966935/asyncio-task-vs-coroutine


class Timer:
    def __init__(self, interval, timer_name, context, callback, initial_wait=None):
        self._interval = interval
        self._initial_wait = initial_wait
        self._name = timer_name
        self._context = context
        self._callback = callback
        self._is_first_call = True
        self._cancelled = False
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        try:
            while not self._cancelled:
                if self._is_first_call and self._initial_wait is not None:
                    await asyncio.sleep(self._initial_wait)
                else:
                    await asyncio.sleep(self._interval)
                await self._callback(self._name, self._context, self)
                self._is_first_call = False
                if self._interval == 0:
                    self._cancelled = True
        except Exception as ex:
            print(ex)

    def cancel(self):
        self._cancelled = True
        self._task.cancel()
