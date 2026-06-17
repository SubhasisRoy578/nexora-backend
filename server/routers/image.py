from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse

from server.services.image_service import generate_image

router = APIRouter()


@router.get("/generate-image/")
async def generate(prompt: str):

    try:

        image_bytes = await generate_image(prompt)

        file_path = "generated_image.png"

        with open(file_path, "wb") as f:
            f.write(image_bytes)

        return FileResponse(
            file_path,
            media_type="image/png"
        )

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )