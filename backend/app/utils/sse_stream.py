# backend/app/utils/sse_stream.py
import asyncio
from sse_starlette import ServerSentEvent
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
class SSEStream:
    def __init__(self) -> None:
        self._queue = asyncio.Queue()
        self._stream_end = object()

    def __aiter__(self):
        return self

    async def __anext__(self):
        data = await self._queue.get()
        logger.info(f"Stream: {repr(data)}")
        if data is self._stream_end:
            raise StopAsyncIteration
        return ServerSentEvent(data=data)

    async def send(self, data):
        await self._queue.put(data)

    async def close(self):
        await self._queue.put(self._stream_end)