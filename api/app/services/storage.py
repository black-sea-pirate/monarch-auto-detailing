import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

import anyio
from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

from app.config import settings

register_heif_opener()
Image.MAX_IMAGE_PIXELS = 50_000_000

MAX_PHOTOS = 10
MAX_VIDEOS = 2
MAX_PHOTO_BYTES = 12 * 1024 * 1024
MAX_VIDEO_BYTES = 50 * 1024 * 1024
MAX_REQUEST_BYTES = 150 * 1024 * 1024
MAX_IMAGE_DIMENSION = 2560
CHUNK_SIZE = 1024 * 1024


class UploadValidationError(ValueError):
    pass


@dataclass(frozen=True)
class StoredUpload:
    kind: str
    original_name: str
    stored_name: str
    content_type: str
    size_bytes: int


def validate_upload_counts(photo_count: int, video_count: int) -> None:
    if photo_count > MAX_PHOTOS:
        raise UploadValidationError(f"You can attach up to {MAX_PHOTOS} photos.")
    if video_count > MAX_VIDEOS:
        raise UploadValidationError(f"You can attach up to {MAX_VIDEOS} videos.")


def _detect_photo_type(header: bytes) -> tuple[str, str] | None:
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp", ".webp"
    if header[4:8] == b"ftyp" and header[8:12] in {
        b"heic",
        b"heix",
        b"hevc",
        b"hevx",
        b"mif1",
        b"msf1",
    }:
        return "image/heic", ".heic"
    return None


def _detect_video_type(header: bytes, declared_type: str) -> tuple[str, str] | None:
    if header[4:8] == b"ftyp":
        if declared_type == "video/quicktime":
            return "video/quicktime", ".mov"
        return "video/mp4", ".mp4"
    if header.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm", ".webm"
    return None


def detect_upload_type(kind: str, header: bytes, declared_type: str) -> tuple[str, str]:
    detected = (
        _detect_photo_type(header) if kind == "photo" else _detect_video_type(header, declared_type)
    )
    if detected is None:
        media_name = "photo" if kind == "photo" else "video"
        raise UploadValidationError(f"One {media_name} uses an unsupported or invalid format.")
    return detected


def upload_root() -> Path:
    root = settings.upload_dir
    if not root.is_absolute():
        root = Path.cwd() / root
    return root.resolve()


def resolve_upload_path(stored_name: str) -> Path:
    root = upload_root()
    candidate = (root / stored_name).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise UploadValidationError("Invalid stored upload path.") from exc
    return candidate


def _normalize_photo(source: Path, destination: Path) -> None:
    try:
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened)
            image.load()
            image.thumbnail(
                (MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION),
                Image.Resampling.LANCZOS,
            )
            if image.mode in {"RGBA", "LA"} or (
                image.mode == "P" and "transparency" in image.info
            ):
                rgba = image.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")
            image.save(
                destination,
                format="JPEG",
                quality=88,
                optimize=True,
                progressive=True,
            )
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError) as exc:
        raise UploadValidationError("The photo could not be safely processed.") from exc


async def _store_one(
    quote_id: uuid.UUID,
    upload: UploadFile,
    kind: str,
    current_total: int,
) -> StoredUpload:
    original_name = Path(upload.filename or f"{kind}-upload").name[:255]
    first_chunk = await upload.read(CHUNK_SIZE)
    if not first_chunk:
        raise UploadValidationError(f"{original_name} is empty.")

    detected_type, extension = detect_upload_type(
        kind,
        first_chunk[:32],
        upload.content_type or "application/octet-stream",
    )
    file_limit = MAX_PHOTO_BYTES if kind == "photo" else MAX_VIDEO_BYTES
    stored_type = "image/jpeg" if kind == "photo" else detected_type
    stored_extension = ".jpg" if kind == "photo" else extension
    relative_path = Path(str(quote_id)) / f"{uuid.uuid4().hex}{stored_extension}"
    destination = resolve_upload_path(relative_path.as_posix())
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_target = (
        destination.with_suffix(f"{destination.suffix}.upload")
        if kind == "photo"
        else destination
    )
    size = 0

    try:
        async with await anyio.open_file(write_target, "wb") as output:
            chunk = first_chunk
            while chunk:
                size += len(chunk)
                if size > file_limit:
                    label = "Photo" if kind == "photo" else "Video"
                    limit_mb = file_limit // (1024 * 1024)
                    raise UploadValidationError(f"{label} files must be {limit_mb} MB or smaller.")
                if current_total + size > MAX_REQUEST_BYTES:
                    limit_mb = MAX_REQUEST_BYTES // (1024 * 1024)
                    raise UploadValidationError(
                        f"All attachments together must be {limit_mb} MB or smaller."
                    )
                await output.write(chunk)
                chunk = await upload.read(CHUNK_SIZE)
        if kind == "photo":
            await anyio.to_thread.run_sync(_normalize_photo, write_target, destination)
            write_target.unlink(missing_ok=True)
            size = destination.stat().st_size
    except Exception:
        write_target.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise

    return StoredUpload(
        kind=kind,
        original_name=original_name,
        stored_name=relative_path.as_posix(),
        content_type=stored_type,
        size_bytes=size,
    )


async def store_quote_upload(
    quote_id: uuid.UUID,
    upload: UploadFile,
    kind: str,
    current_total: int,
) -> StoredUpload:
    """Store one independently uploaded file while preserving its original bytes."""
    if kind not in {"photo", "video"}:
        raise UploadValidationError("Upload kind must be photo or video.")
    try:
        return await _store_one(quote_id, upload, kind, current_total)
    finally:
        await upload.close()


async def purge_quote_files(quote_id: uuid.UUID) -> None:
    root = upload_root()
    target = (root / str(quote_id)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise UploadValidationError("Invalid quote storage path.") from exc
    if target.exists():
        await anyio.to_thread.run_sync(shutil.rmtree, target)


async def purge_stored_upload(stored_name: str) -> None:
    path = resolve_upload_path(stored_name)
    if path.exists():
        await anyio.to_thread.run_sync(path.unlink)
    root = upload_root()
    parent = path.parent
    if parent != root and parent.exists() and not any(parent.iterdir()):
        await anyio.to_thread.run_sync(parent.rmdir)
