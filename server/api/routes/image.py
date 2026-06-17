"""
Nexora AI — Image Generation Router
Multi-provider image generation: DALL-E 3, Stable Diffusion, Flux.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
import httpx

from app.config import settings
from app.models.user import User
from app.schemas.schemas import ImageGenerationRequest, ImageGenerationResponse
from app.middleware.auth_middleware import get_current_user, require_subscription

router = APIRouter()
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_dalle(payload: ImageGenerationRequest) -> ImageGenerationResponse:
    """Generate image using OpenAI DALL-E 3."""
    response = await openai_client.images.generate(
        model=payload.model if payload.model.startswith("dall-e") else "dall-e-3",
        prompt=payload.prompt,
        size=payload.size,  # type: ignore
        quality=payload.quality,  # type: ignore
        style=payload.style,  # type: ignore
        n=payload.n,
        response_format="url",
    )
    images = [img.url for img in response.data if img.url]
    revised = response.data[0].revised_prompt if response.data else None

    return ImageGenerationResponse(
        images=images,
        prompt=payload.prompt,
        model=payload.model,
        revised_prompt=revised,
        created_at=datetime.utcnow(),
    )


async def generate_stability(payload: ImageGenerationRequest) -> ImageGenerationResponse:
    """Generate image using Stability AI."""
    if not settings.STABILITY_API_KEY:
        raise HTTPException(status_code=503, detail="Stability AI not configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers={
                "Authorization": f"Bearer {settings.STABILITY_API_KEY}",
                "Accept": "application/json",
            },
            json={
                "text_prompts": [
                    {"text": payload.prompt, "weight": 1},
                    *(
                        [{"text": payload.negative_prompt, "weight": -1}]
                        if payload.negative_prompt else []
                    ),
                ],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "steps": 30,
                "samples": payload.n,
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

    images = []
    for artifact in data.get("artifacts", []):
        if artifact.get("finishReason") == "SUCCESS":
            import base64
            # Return as data URL
            b64 = artifact["base64"]
            images.append(f"data:image/png;base64,{b64}")

    return ImageGenerationResponse(
        images=images,
        prompt=payload.prompt,
        model="stable-diffusion-xl",
        created_at=datetime.utcnow(),
    )


async def generate_flux(payload: ImageGenerationRequest) -> ImageGenerationResponse:
    """Generate image using Flux via fal.ai."""
    if not settings.FAL_API_KEY:
        raise HTTPException(status_code=503, detail="fal.ai not configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://fal.run/fal-ai/flux/schnell",
            headers={
                "Authorization": f"Key {settings.FAL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "prompt": payload.prompt,
                "num_images": payload.n,
                "image_size": "landscape_4_3",
            },
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()

    images = [img["url"] for img in data.get("images", [])]

    return ImageGenerationResponse(
        images=images,
        prompt=payload.prompt,
        model="flux-schnell",
        created_at=datetime.utcnow(),
    )


@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(
    payload: ImageGenerationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate images using the best available provider.
    Priority: DALL-E 3 → Flux → Stability AI
    """
    try:
        if payload.model == "flux" and settings.FAL_API_KEY:
            return await generate_flux(payload)
        elif payload.model == "stable-diffusion" and settings.STABILITY_API_KEY:
            return await generate_stability(payload)
        else:
            return await generate_dalle(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")


@router.post("/variations")
async def create_image_variation(
    current_user: User = Depends(require_subscription("pro")),
):
    """Create variations of an uploaded image (Pro feature)."""
    return {"message": "Upload an image to create variations (coming soon)"}


@router.post("/edit")
async def edit_image(
    current_user: User = Depends(require_subscription("pro")),
):
    """Edit an image with a text instruction (inpainting)."""
    return {"message": "Image editing with inpainting (coming soon)"}