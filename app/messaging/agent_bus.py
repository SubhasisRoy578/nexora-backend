import asyncio


class AgentBus:

    def __init__(self):

        self.queue = asyncio.Queue()

    async def publish(
        self,
        sender,
        payload
    ):

        await self.queue.put(
            {
                "sender": sender,
                "payload": payload
            }
        )

    async def consume(self):

        return await self.queue.get()


agent_bus = AgentBus()