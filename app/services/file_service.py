import os
import aiofiles
from uuid import uuid4

UPLOAD_DIR = "app/uploads/raw"

os.makedirs(UPLOAD_DIR, exist_ok=True)


async def save_upload_file(file):

    unique_name = f"{uuid4()}_{file.filename}"

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_name
    )

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    return file_path