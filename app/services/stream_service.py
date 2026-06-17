import asyncio
from typing import AsyncGenerator


async def fake_stream(text: str) -> AsyncGenerator[str, None]:
    """
    Simulates token streaming response.
    """

    words = text.split()

    for word in words:
        yield word + " "
        await asyncio.sleep(0.03)