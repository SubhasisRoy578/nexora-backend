import os

from langchain_groq import ChatGroq

class LLMService:

    def __init__(self):

        self.llm = ChatGroq(
            model="llama3-70b-8192",
            api_key=os.getenv("GROQ_API_KEY")
        )

    async def generate(
        self,
        prompt: str
    ):

        response = self.llm.invoke(
            prompt
        )

        return response.content


llm_service = LLMService()