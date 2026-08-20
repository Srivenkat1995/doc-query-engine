from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Invoice
from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.storage import Storage, get_storage
from app.upload_validation import (
    UploadValidationCode,
    UploadValidationError,
    validate_upload,
)

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)) -> Invoice:
    invoice = Invoice(**payload.model_dump())
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.post(
    "/upload",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: Storage = Depends(get_storage),
) -> Invoice:
    content = await file.read()
    mime_type = file.content_type or ""
    try:
        validate_upload(content, mime_type)
    except UploadValidationError as error:
        response_status = (
            status.HTTP_413_CONTENT_TOO_LARGE
            if error.code == UploadValidationCode.FILE_TOO_LARGE
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=response_status,
            detail={"code": error.code.value, "message": error.message},
        ) from error

    invoice_id = str(uuid4())
    storage_key = f"invoices/{invoice_id}"
    try:
        storage.put(storage_key, content)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "storage_unavailable",
                "message": "File storage is unavailable",
            },
        ) from error

    invoice = Invoice(
        id=invoice_id,
        original_filename=file.filename or "unnamed-upload",
        mime_type=mime_type.strip().lower(),
        size_bytes=len(content),
        storage_key=storage_key,
    )
    try:
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
    except Exception as error:
        db.rollback()
        storage.delete(storage_key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "persistence_failed",
                "message": "Invoice could not be saved",
            },
        ) from error
    return invoice


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)) -> Invoice:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    return invoice