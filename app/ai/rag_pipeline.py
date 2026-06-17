from app.ai.memory_engine import retrieve_memory

def build_context(user_message: str):

    memories = retrieve_memory(user_message)

    context = "\n".join(memories)

    return f"""
Relevant Memory:
{context}

User Message:
{user_message}
"""