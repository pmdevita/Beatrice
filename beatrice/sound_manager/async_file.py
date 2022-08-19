import asyncio
import traceback
import typing
import weakref
from io import BytesIO
from pathlib import Path
import aiohttp
import aiofiles
from .data import AudioFile


class AsyncFileManager:
    def __init__(self, cache_path: typing.Optional[Path] = None, max_preload: int = 3):
        self.cache_path = cache_path
        self.max_preload = max_preload
        self.session = aiohttp.ClientSession()
        self.files = []
        self._background_tasks = set()

    def start_background_task(self, coro):
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def open(self, audio_file: AudioFile):
        file = AsyncFile(self, audio_file)
        self.files.append(weakref.ref(file))
        self.start_background_task(self.preload())
        return file

    def _flush(self):
        self.files = [x for x in self.files if x() is not None]

    async def preload(self):
        # Start preloading extra files in queue if we can
        current_downloads = 0
        self._flush()
        for f in self.files:
            file = f()
            if file.download_job is not None and not file.downloaded_file:
                current_downloads += 1
        if current_downloads < self.max_preload:
            downloads_left = self.max_preload - current_downloads
            for f in self.files:
                if downloads_left == 0:
                    break
                file = f()
                if file.download_job is None and not file.downloaded_file:
                    print("Preloading", file)
                    await file.open()
                    downloads_left -= 1

    def __del__(self):
        for task in list(self._background_tasks):
            task.cancel()


class AsyncFile:
    CHUNK_SIZE = 4096
    BUFFER_THRESHOLD = 1024 * 1024

    def __init__(self, manager: AsyncFileManager, audio_file: AudioFile):
        self.manager = manager
        self.file_path = audio_file.file
        self.cache_name = audio_file.cache_name
        self.title = audio_file.title
        self.buffer = BytesIO()
        self.buffers = [BytesIO()]
        self.file = None
        self.has_seeked_file = False
        self.cursor = 0
        self.size = 0
        self.downloaded_file = False  # Has file completely and fully downloaded?
        self.download_job = None

        # Read needs to await the download start in order to potentially have data to read
        self.read = self._preload_read
        self._read_ready = asyncio.Event()   # Is ready to start reading?

    async def open(self):
        if not self.download_job:
            self.download_job = asyncio.create_task(self._open())

    async def _open(self):
        try:
            if self.file_path.startswith("http"):
                async with self.manager.session.get(self.file_path) as resp:
                    self._read_ready.set()
                    # Use file cache
                    if self.cache_name and self.manager.cache_path:
                        f = await aiofiles.open(self.manager.cache_path / self.cache_name, 'wb')
                        await self._download_with_file(resp, f)
                        await f.close()
                        self.file = await aiofiles.open(self.manager.cache_path / self.cache_name, 'rb')
                        self.buffer = None
                    # Only read from memory
                    else:
                        await self._download_only_cache(resp)
            else:
                self.file = await aiofiles.open(self.file_path, 'rb')
                self.buffer = None
                self._read_ready.set()
            print("Download finished for", self)
        except asyncio.exceptions.CancelledError:
            print("Cancelling download")
        except:
            print(traceback.format_exc())
        self.manager.start_background_task(self.manager.preload())
        self.downloaded_file = True

    async def _download_with_file(self, resp, f):
        async for chunk in resp.content.iter_chunked(self.CHUNK_SIZE):
            # print("Downloading chunk...", self.size)
            await f.write(chunk)
            self.buffer.write(chunk)
            self.size += len(chunk)
            # await asyncio.sleep(.1)

    async def _download_only_cache(self, resp):
        async for chunk in resp.content.iter_chunked(self.CHUNK_SIZE):
            # print("Downloading chunk...", self.size, self.buffer.getbuffer().nbytes)
            self.buffer.seek(self.buffer.getbuffer().nbytes)
            self.buffer.write(chunk)
            self.size += len(chunk)
            try:
                assert self.size == self.buffer.getbuffer().nbytes
            except AssertionError as e:
                print("WTF", len(chunk), self.size, self.buffer.getbuffer().nbytes)
                self.size = self.buffer.getbuffer().nbytes

    async def _write_to_buffer(self, chunk):
        if len(self.buffers) == 1:
            if self.buffers[0].getbuffer().nbytes > self.BUFFER_THRESHOLD:
                self.buffers.append(BytesIO())
        self.buffers[-1].write(chunk)
        self.size += self.CHUNK_SIZE

    async def _preload_read(self, chunk: int):
        await self._read_ready.wait()
        self.read = self._after_load_read
        return await self._after_load_read(chunk)

    async def _after_load_read(self, chunk: int):
        if self.buffer:
            while self.buffer.getbuffer().nbytes - self.cursor < chunk and not self.downloaded_file:
                # print("Waiting for chunk...")
                await asyncio.sleep(.2)
        if not self.file:
            # print("Retrieving from buffer", self.cursor, self.buffer.getbuffer().nbytes, self.size)
            self.buffer.seek(self.cursor)
            data = self.buffer.read(chunk)
        else:
            if not self.has_seeked_file:
                print("Transferring from buffer to file")
                await self.file.seek(self.cursor)
                self.has_seeked_file = True
            data = await self.file.read(chunk)
        self.cursor += len(data)
        return data

    def finished_reading(self):
        if self.downloaded_file:
            return self.cursor >= self.size
        return False

    async def close(self):
        if self.download_job:
            self.download_job.cancel()
        if self.file:
            await self.file.close()

    def __del__(self):
        if self.download_job:
            self.download_job.cancel()

    def __repr__(self):
        return f"AsyncFile({self.title})"
