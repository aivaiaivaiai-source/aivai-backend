from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_current_user, get_voice_service
from app.core.exceptions import AppException
from app.schemas.user import UserRead
from app.schemas.voice import VoiceCommandRequest, VoiceCommandResponse
from app.services.voice_service import VoiceService

router = APIRouter()

_MAX_AUDIO_BYTES = 10 * 1024 * 1024
_ALLOWED_AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a"}
_ALLOWED_AUDIO_CONTENT_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp4",
    "audio/x-m4a",
}


async def _read_upload_capped(upload: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise AppException("Размер аудиофайла не должен превышать 10 МБ", status_code=400)
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("/command", response_model=VoiceCommandResponse)
async def post_voice_command(
    body: VoiceCommandRequest,
    user: UserRead = Depends(get_current_user),
    voice: VoiceService = Depends(get_voice_service),
) -> VoiceCommandResponse:
    return await voice.handle_command(body, user)


@router.post("/audio", response_model=VoiceCommandResponse)
async def post_voice_audio(
    file: UploadFile = File(...),
    user: UserRead = Depends(get_current_user),
    voice: VoiceService = Depends(get_voice_service),
) -> VoiceCommandResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_AUDIO_SUFFIXES:
        raise AppException(
            "Допустимые форматы файла: wav, mp3, m4a",
            status_code=400,
        )
    if file.content_type not in _ALLOWED_AUDIO_CONTENT_TYPES:
        raise AppException("Неверный тип аудиофайла", status_code=400)

    audio_bytes = await _read_upload_capped(file, _MAX_AUDIO_BYTES)
    if not audio_bytes:
        raise AppException("Аудиофайл пустой", status_code=400)

    return await voice.handle_audio(audio_bytes, user)
