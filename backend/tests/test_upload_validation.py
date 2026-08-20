import pytest

from app.upload_validation import (
    MAX_UPLOAD_BYTES,
    UploadValidationCode,
    UploadValidationError,
    validate_upload,
)


@pytest.mark.parametrize(
    "mime_type",
    ["application/pdf", "image/jpeg", "image/png", " IMAGE/PNG "],
)
def test_validate_upload_accepts_supported_types(mime_type: str) -> None:
    validate_upload(b"invoice bytes", mime_type)


@pytest.mark.parametrize(
    "mime_type",
    ["application/zip", "text/plain", "image/gif", ""],
)
def test_validate_upload_rejects_unsupported_types(mime_type: str) -> None:
    with pytest.raises(UploadValidationError) as error:
        validate_upload(b"invoice bytes", mime_type)

    assert error.value.code == UploadValidationCode.UNSUPPORTED_TYPE


def test_validate_upload_rejects_empty_file() -> None:
    with pytest.raises(UploadValidationError) as error:
        validate_upload(b"", "application/pdf")

    assert error.value.code == UploadValidationCode.EMPTY_FILE


def test_validate_upload_rejects_file_over_5mb() -> None:
    with pytest.raises(UploadValidationError) as error:
        validate_upload(b"x" * (MAX_UPLOAD_BYTES + 1), "application/pdf")

    assert error.value.code == UploadValidationCode.FILE_TOO_LARGE


def test_validate_upload_accepts_file_at_5mb_limit() -> None:
    validate_upload(b"x" * MAX_UPLOAD_BYTES, "application/pdf")
