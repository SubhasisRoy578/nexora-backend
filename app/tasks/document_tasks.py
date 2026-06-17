import asyncio
async def process_document(
    file_path: str
):
    await asyncio.sleep(3)
    return {
        "file": file_path,
        "status":
        "processed"

    }