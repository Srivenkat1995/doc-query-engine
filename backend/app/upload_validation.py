from __future__ import annotations

from enum import Enum
from typing import FrozenSet

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
SUPPORTED_MIME_TYPES: FrozenSet[str] = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
    }
)


class UploadValidationCode(str, Enum):
    UNSUPPORTED_TYPE = "unsupported_type"
    EMPTY_FILE = "empty_file"
    FILE_TOO_LARGE = "file_too_large"


class UploadValidationError(ValueError):
    """A file failed one of the upload safety rules."""

    def __init__(self, code: UploadValidationCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def validate_upload(content: bytes, mime_type: str) -> None:
    """Validate upload bytes and MIME type before storage or persistence."""

    normalized_mime_type = mime_type.strip().lower()
    if normalized_mime_type not in SUPPORTED_MIME_TYPES:
        raise UploadValidationError(
            UploadValidationCode.UNSUPPORTED_TYPE,
            "Only PDF, JPEG, and PNG files are supported",
        )
    if not content:
        raise UploadValidationError(
            UploadValidationCode.EMPTY_FILE,
            "The uploaded file is empty",
        )
    if len(content) > MAX_UPLOAD_BYTES:
        raise UploadValidationError(
            UploadValidationCode.FILE_TOO_LARGE,
            "The uploaded file must be no larger than 5MB",
        )
