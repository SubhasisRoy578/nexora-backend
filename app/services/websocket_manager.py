from fastapi import WebSocket
from typing import Dict, List


class ConnectionManager:

    def __init__(self):

        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(
        self,
        user_id: str,
        websocket: WebSocket
    ):

        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(
            websocket
        )

    def disconnect(
        self,
        user_id: str,
        websocket: WebSocket
    ):

        if user_id in self.active_connections:

            if websocket in self.active_connections[user_id]:

                self.active_connections[user_id].remove(
                    websocket
                )

            if len(self.active_connections[user_id]) == 0:

                del self.active_connections[user_id]

    async def send_personal_message(
        self,
        message: str,
        user_id: str
    ):

        if user_id not in self.active_connections:
            return

        for connection in self.active_connections[user_id]:

            await connection.send_text(message)

    async def broadcast(
        self,
        message: str
    ):

        for users in self.active_connections.values():

            for connection in users:

                await connection.send_text(message)


manager = ConnectionManager()