from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
import asyncio


class StreamingChatEngine:

    def __init__(self, llm):
        self.llm = llm

    async def stream_response(
        self,
        message: str
    ):

        async def generate():

            try:

                response = self.llm.stream(
                    [HumanMessage(content=message)]
                )

                for chunk in response:

                    if hasattr(chunk, "content"):

                        content = chunk.content

                        if content:
                            yield content

                        await asyncio.sleep(0.01)

            except Exception as e:

                yield f"\n\nStreaming Error: {str(e)}"

        return StreamingResponse(
            generate(),
            media_type="text/plain"
        )

    async def normal_response(
        self,
        message: str
    ):

        try:

            response = self.llm.invoke(
                [HumanMessage(content=message)]
            )

            return {
                "response": response.content
            }

        except Exception as e:

            return {
                "error": str(e)
            }