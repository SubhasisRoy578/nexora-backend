import asyncio

from app.workers.background_worker import (
    BackgroundWorker
)


class WorkerManager:

    def __init__(self):

        self.worker = BackgroundWorker()

    async def start(self):

        asyncio.create_task(
            self.worker.start()
        )


worker_manager = WorkerManager()