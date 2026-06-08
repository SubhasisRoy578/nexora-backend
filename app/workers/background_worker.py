import asyncio

from app.messaging.agent_bus import (
    agent_bus
)


class BackgroundWorker:

    async def start(self):

        while True:

            task = await agent_bus.consume()

            print(
                "BACKGROUND TASK:",
                task
            )

            await asyncio.sleep(1)