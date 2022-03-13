import asyncio
import io
import logging
from nextcord.types.voice import (
        GuildVoiceState as GuildVoiceStatePayload,
        VoiceServerUpdate as VoiceServerUpdatePayload,
        SupportedModes,
    )
from nextcord.utils import MISSING

import nextcord
from nextcord import opus


class AsyncFFmpegAudio(nextcord.AudioSource):
    def __init__(self, source):
        self._source = source
        self._process = None
        self._buffer = io.BytesIO()

    async def start(self):
        args = ["ffmpeg", "-i", self._source, '-f', 's16le', '-ar', '48000', '-ac', '2', '-loglevel', 'warning', "-"]
        self._process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE)

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

    def cleanup(self) -> None:
        if self._process:
            try:
                self._process.terminate()
            except ProcessLookupError:
                pass


class AsyncFFmpegPCMWrapper(nextcord.FFmpegPCMAudio):
    async def start(self):
        pass

    async def read(self) -> bytes:
        return super().read()


_log = logging.getLogger(__name__)


class AsyncVoiceClient(nextcord.VoiceClient):
    async def on_voice_server_update(self, data: VoiceServerUpdatePayload) -> None:
        if self._voice_server_complete.is_set():
            _log.info('Ignoring extraneous voice server update.')
            return

        self.token = data.get('token')
        self.server_id = int(data['guild_id'])
        endpoint = data.get('endpoint')

        if endpoint is None or self.token is None:
            _log.warning('Awaiting endpoint... This requires waiting. ' \
                        'If timeout occurred considering raising the timeout and reconnecting.')
            return

        self.endpoint, _, _ = endpoint.rpartition(':')
        if self.endpoint.startswith('wss://'):
            # Just in case, strip it off since we're going to add it later
            self.endpoint = self.endpoint[6:]

        # This gets set later
        self.endpoint_ip = MISSING

        self.socket = asyncio.open_connection()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)

        if not self._handshaking:
            # If we're not handshaking then we need to terminate our previous connection in the websocket
            await self.ws.close(4000)
            return

        self._voice_server_complete.set()

    async def disconnect(self, *, force: bool = False) -> None:
        """|coro|

        Disconnects this voice client from voice.
        """
        if not force and not self.is_connected():
            return

        self.stop()
        self._connected.clear()

        try:
            if self.ws:
                await self.ws.close()

            await self.voice_disconnect()
        finally:
            self.cleanup()
            if self.socket:
                self.socket.close()

    def send_audio_packet(self, data: bytes, *, encode: bool = True) -> None:
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
            encoded_data = self.encoder.encode(data, self.encoder.SAMPLES_PER_FRAME)
        else:
            encoded_data = data
        packet = self._get_voice_packet(encoded_data)
        try:
            self.socket.sendto(packet, (self.endpoint_ip, self.voice_port))
        except BlockingIOError:
            _log.warning('A packet has been dropped (seq: %s, timestamp: %s)', self.sequence, self.timestamp)

        self.checked_add('timestamp', opus.Encoder.SAMPLES_PER_FRAME, 4294967295)
