import asyncio
from datetime import datetime, timedelta
import pytz


# What are tasks for? https://stackoverflow.com/questions/57966935/asyncio-task-vs-coroutine

class TimerTask:
    def __init__(self, timer, time: datetime, callback, repeat=None):
        self.timer = timer
        self.time = time
        self.callback = callback
        self.repeat = repeat

    async def callback(self):
        await self.callback()
        if self.repeat:
            self.time += self.repeat
            # Readd instead of recreate so API doesn't lose handler to the task
            self.timer._readd_task(self)

    def cancel(self):
        self.timer.cancel(self)


class Timer:
    def __init__(self, discord):
        self.discord = discord
        self.tasks = []
        self.task_dict = {}
        self._tasks_dirty = False
        self._current_timer = None
        self._running_task = None
        self._balancing_task = None
        self.timezone = pytz.timezone(self.discord.config["general"]["locale"])

    async def _balance_tasks(self):
        if not self._tasks_dirty:
            return

        self.tasks = sorted(self.tasks, key=lambda x: x.time)
        next_time = self.tasks[0].time
        if self._current_timer:
            self._current_timer.cancel()
        self._current_timer = asyncio.ensure_future(self._timer_job(next_time))
        self._tasks_dirty = False
        self._balancing_task = None

    async def _timer_job(self, time: datetime):
        till_time = time - datetime.now(self.timezone)
        till_time_secs = till_time.total_seconds()
        if till_time_secs > 0:
            await asyncio.sleep(till_time_secs)
        self._running_task = asyncio.ensure_future(self._run_jobs())
        self._current_timer = None

    async def _run_jobs(self):
        now = datetime.now(self.timezone)
        jobs_to_run = []
        # Bit awkward but avoids potentially unsafe getting of index 0
        while True:
            if len(self.tasks) > 0:
                if self.tasks[0].time <= now:
                    jobs_to_run.append(self.tasks.pop(0))
                    continue
            break
        self._tasks_dirty = True
        for job in jobs_to_run:
            try:
                await job.callback()
            except Exception as e:
                print(e)
        await self._balance_tasks()
        self._running_task = None

    def schedule_task(self, time: datetime, callback, repeat: timedelta = None):
        if time.tzinfo is None:
            time = time.astimezone(self.timezone)
        task = TimerTask(self, time, callback, repeat)
        self.tasks.append(task)
        self._tasks_dirty = True
        self._balancing_task = asyncio.ensure_future(self._balance_tasks())
        return task

    def _readd_task(self, task: TimerTask):
        self.tasks.append(task)
        self._tasks_dirty = True
        self._balancing_task = asyncio.ensure_future(self._balance_tasks())

    def cancel(self, task):
        self.tasks.remove(task)
        self._tasks_dirty = True
        self._balancing_task = asyncio.ensure_future(self._balance_tasks())
