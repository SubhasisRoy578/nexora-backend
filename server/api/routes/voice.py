"""
Nexora AI — Voice Router
Text-to-Speech (ElevenLabs) and Speech-to-Text (OpenAI Whisper).
Streams audio back to the client.
"""

import io
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from openai import AsyncOpenAI

from app.config import settings
from app.models.user import User
from app.schemas.schemas import TextToSpeechRequest, VoiceListResponse
from app.middleware.auth_middleware import get_current_user

router = APIRouter()
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


@router.post("/synthesize")
async def text_to_speech(
    payload: TextToSpeechRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Convert text to speech using ElevenLabs.
    Returns audio stream (MP3).
    """
    if not settings.ELEVENLABS_API_KEY:
        # Fallback to OpenAI TTS
        return await _openai_tts(payload.text)

    from elevenlabs.client import ElevenLabs

    client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

    audio_generator = client.text_to_speech.convert(
        voice_id=payload.voice_id,
        model_id=payload.model,
        text=payload.text,
        voice_settings={
            "stability": payload.stability,
            "similarity_boost": payload.similarity_boost,
        },
    )

    def generate():
        for chunk in audio_generator:
            if chunk:
                yield chunk

    return StreamingResponse(
        generate(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=speech.mp3",
            "X-Voice-Model": payload.model,
        },
    )


async def _openai_tts(text: str) -> StreamingResponse:
    """Fallback TTS using OpenAI TTS-1."""
    response = await openai_client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=text[:4096],
    )

    async def stream():
        async for chunk in response.aiter_bytes(chunk_size=4096):
            yield chunk

    return StreamingResponse(
        stream(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=speech.mp3"},
    )


@router.post("/transcribe")
async def speech_to_text(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Transcribe speech to text using OpenAI Whisper.
    Accepts: mp3, mp4, mpeg, mpga, m4a, wav, webm (max 25MB).
    """
    allowed = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm", ".ogg"}
    from pathlib import Path
    suffix = Path(audio.filename or "audio.webm").suffix.lower()

    if suffix not in allowed:
        raise HTTPException(status_code=415, detail=f"Audio format {suffix} not supported")

    content = await audio.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio file exceeds 25MB limit")

    # Send to Whisper
    audio_file = io.BytesIO(content)
    audio_file.name = audio.filename or f"audio{suffix}"

    transcript = await openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",
        timestamp_granularities=["word"],
    )

    return {
        "text": transcript.text,
        "language": getattr(transcript, "language", "en"),
        "duration": getattr(transcript, "duration", None),
        "words": getattr(transcript, "words", []),
    }


@router.get("/voices", response_model=VoiceListResponse)
async def list_voices(current_user: User = Depends(get_current_user)):
    """List available ElevenLabs voices."""
    if not settings.ELEVENLABS_API_KEY:
        # Return OpenAI voices as fallback
        return {
            "voices": [
                {"id": "alloy", "name": "Alloy", "provider": "openai"},
                {"id": "echo", "name": "Echo", "provider": "openai"},
                {"id": "fable", "name": "Fable", "provider": "openai"},
                {"id": "onyx", "name": "Onyx", "provider": "openai"},
                {"id": "nova", "name": "Nova", "provider": "openai"},
                {"id": "shimmer", "name": "Shimmer", "provider": "openai"},
            ]
        }

    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
    voices_response = client.voices.get_all()

    return {
        "voices": [
            {
                "id": v.voice_id,
                "name": v.name,
                "category": getattr(v, "category", ""),
                "provider": "elevenlabs",
                "preview_url": getattr(v, "preview_url", None),
            }
            for v in voices_response.voices
        ]
    }