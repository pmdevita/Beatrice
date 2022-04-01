import array
import asyncio
import ctypes
import io
import logging
import typing

import nextcord
from nextcord import opus
from nextcord.opus import Encoder, _lib, c_int16_ptr


class AsyncFFmpegAudio(nextcord.AudioSource):
    def __init__(self, source):
        self._source = source
        self._process = None
        self._buffer = io.BytesIO()

    async def start(self):
        args = ["ffmpeg", "-i", self._source, '-f', 's16le', '-ar', '48000', '-ac', '2', '-loglevel', 'warning', "-"]
        self._process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stdin=asyncio.subprocess.PIPE)

    async def read(self) -> bytes:
        data = await self._process.stdout.read(3840)
        if not data:
            await self._process.wait()
            self._process = None
            return bytes(0)
        else:
            if len(data) < 3840:
                data += bytes(3840 - len(data))  # todo: would be better to do within numpy
            return data

    def close(self) -> None:
        if self._process:
            try:
                print("Terminating...")
                # IDK why it needs to be killed but terminating doesn't work. Maybe we need to communicate() and read
                # out all of the data so it can terminate?
                self._process.kill()
            except ProcessLookupError:
                pass

    def __del__(self):
        print("Received delete, terminating...")
        self.close()


class AsyncFFmpegPCMWrapper(nextcord.FFmpegPCMAudio):
    async def start(self):
        pass

    async def read(self) -> bytes:
        return super().read()


_log = logging.getLogger(__name__)


class AsyncVoiceClient(nextcord.VoiceClient):
    async def prepare_audio_packet(self, data: bytes, *, encode: bool = True) -> None:
        self.checked_add('sequence', 1, 65535)
        if encode:
            encoded_data = await self.encoder.encode(data, self.encoder.SAMPLES_PER_FRAME)
        else:
            encoded_data = data
        packet = self._get_voice_packet(encoded_data)
        self.checked_add('timestamp', opus.Encoder.SAMPLES_PER_FRAME, 4294967295)
        return packet

    async def actually_send_audio_packet(self, packet: bytes):
        try:
            self.socket.sendto(packet, (self.endpoint_ip, self.voice_port))
        except BlockingIOError:
            _log.warning('A packet has been dropped (seq: %s, timestamp: %s)', self.sequence, self.timestamp)

    async def send_audio_packet(self, data: bytes, *, encode: bool = True) -> None:
        """Sends an audio packet composed of the data.

        You must be connected to play audio.

        Parameters
        ----------
        data: :class:`bytes`
            The :term:`py:bytes-like object` denoting PCM or Opus voice data.
        encode: :class:`bool`
            Indicates if ``data`` should be encoded into Opus.

        Raises
        -------
        ClientException
            You are not connected.
        opus.OpusError
            Encoding the data failed.
        """

        self.checked_add('sequence', 1, 65535)
        if encode:
            encoded_data = await self.encoder.encode(data, self.encoder.SAMPLES_PER_FRAME)
            if not encoded_data:
                return
        else:
            encoded_data = data
        packet = self._get_voice_packet(encoded_data)
        try:
            self.socket.sendto(packet, (self.endpoint_ip, self.voice_port))
            # await self.async_socket.send(packet)
        except BlockingIOError:
            _log.warning('A packet has been dropped (seq: %s, timestamp: %s)', self.sequence, self.timestamp)

        self.checked_add('timestamp', opus.Encoder.SAMPLES_PER_FRAME, 4294967295)


class AsyncEncoder(Encoder):
    def __init__(self, executor, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.executor = executor
        self.loop = loop

    def actually_encode(self, pcm: bytes, frame_size: int):
        max_data_bytes = len(pcm)
        # bytes can be used to reference pointer
        pcm_ptr = ctypes.cast(pcm, c_int16_ptr)  # type: ignore
        data = (ctypes.c_char * max_data_bytes)()
        ret = _lib.opus_encode(self._state, pcm_ptr, frame_size, data, max_data_bytes)
        return ret

    async def encode(self, pcm: bytes, frame_size: int) -> typing.Optional[bytes]:
        max_data_bytes = len(pcm)
        # bytes can be used to reference pointer
        pcm_ptr = ctypes.cast(pcm, c_int16_ptr)  # type: ignore
        data = (ctypes.c_char * max_data_bytes)()
        # print("encoding...")
        # ret = await self.loop.run_in_executor(self.executor, self.actually_encode, pcm, frame_size)
        task = self.loop.run_in_executor(self.executor, _lib.opus_encode, self._state, pcm_ptr, frame_size, data,
                                              max_data_bytes)
        # ret = await self.loop.run_in_executor(self.executor, _lib.opus_encode, self._state, pcm_ptr, frame_size, data,
        #                                       max_data_bytes)
        # ret = _lib.opus_encode(self._state, pcm_ptr, frame_size, data, max_data_bytes)

        try:
            ret = await asyncio.wait_for(task, timeout=0.020)
        except asyncio.TimeoutError:
            print("Hey it didn't finish!!!!")
            return None

        # array can be initialized with bytes but mypy doesn't know
        return array.array('b', data[:ret]).tobytes()  # type: ignore
