from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import (
    ExtractedFieldRecord,
    ExtractionRecord,
    Invoice,
    LineItemRecord,
    ProcessingJob,
)
from app.schemas.dispatch import DispatchResponse
from app.schemas.extraction import (
    CitationResponse,
    ExtractedFieldResponse,
    ExtractionResponse,
    LineItemResponse,
)
from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.schemas.job import JobCreate, JobResponse
from app.schemas.status import ProcessingStatusResponse
from app.storage import Storage, get_storage
from app.task_context import ProcessingTaskPayload, TaskContext
from app.tracing import get_trace_id
from app.upload_validation import (
    UploadValidationCode,
    UploadValidationError,
    validate_upload,
)
from app.worker import celery_app

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


@router.post(
    "/{invoice_id}/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_processing_job(
    invoice_id: str,
    payload: JobCreate,
    response: Response,
    db: Session = Depends(get_db),
) -> ProcessingJob:
    if db.get(Invoice, invoice_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    existing_job = db.scalar(
        select(ProcessingJob).where(
            ProcessingJob.invoice_id == invoice_id,
            ProcessingJob.idempotency_key == payload.idempotency_key,
        )
    )
    if existing_job is not None:
        response.status_code = status.HTTP_200_OK
        return existing_job

    job = ProcessingJob(invoice_id=invoice_id, **payload.model_dump())
    db.add(job)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing_job = db.scalar(
            select(ProcessingJob).where(
                ProcessingJob.invoice_id == invoice_id,
                ProcessingJob.idempotency_key == payload.idempotency_key,
            )
        )
        if existing_job is None:
            raise
        response.status_code = status.HTTP_200_OK
        return existing_job
    db.refresh(job)
    return job


@router.post(
    "/{invoice_id}/jobs/{job_id}/dispatch",
    response_model=DispatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def dispatch_processing_job(
    invoice_id: str,
    job_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> DispatchResponse:
    job = db.get(ProcessingJob, job_id)
    invoice = db.get(Invoice, invoice_id)
    if job is None or invoice is None or job.invoice_id != invoice_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found",
        )
    if not invoice.storage_key:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "missing_storage_key",
                "message": "Invoice has no stored file",
            },
        )

    trace_id = get_trace_id(request)
    payload = ProcessingTaskPayload(
        context=TaskContext(
            trace_id=trace_id,
            invoice_id=invoice_id,
            job_id=job_id,
        ),
        storage_key=invoice.storage_key,
    )
    try:
        celery_app.send_task(
            "app.worker.process_invoice",
            args=[payload.to_payload()],
            kwargs={},
            task_id=job_id,
            queue="documents",
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "queue_unavailable", "message": "Job queue is unavailable"},
        ) from error
    return DispatchResponse(
        job_id=job_id,
        invoice_id=invoice_id,
        accepted=True,
        trace_id=trace_id,
    )


@router.get(
    "/{invoice_id}/jobs/{job_id}/status",
    response_model=ProcessingStatusResponse,
)
def get_processing_status(
    invoice_id: str,
    job_id: str,
    db: Session = Depends(get_db),
) -> ProcessingStatusResponse:
    invoice = db.get(Invoice, invoice_id)
    job = db.get(ProcessingJob, job_id)
    if invoice is None or job is None or job.invoice_id != invoice_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found",
        )
    return ProcessingStatusResponse(
        invoice_id=invoice.id,
        job_id=job.id,
        invoice_status=invoice.status,
        job_status=job.status,
        attempt_count=job.attempt_count,
        failure_reason=job.failure_reason,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/{invoice_id}/extraction", response_model=ExtractionResponse)
def get_extraction(
    invoice_id: str,
    db: Session = Depends(get_db),
) -> ExtractionResponse:
    if db.get(Invoice, invoice_id) is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    extraction = db.get(ExtractionRecord, invoice_id)
    if extraction is None:
        raise HTTPException(status_code=404, detail="Extraction not found")

    fields = db.scalars(
        select(ExtractedFieldRecord)
        .where(ExtractedFieldRecord.invoice_id == invoice_id)
        .order_by(ExtractedFieldRecord.name)
    ).all()
    line_items = db.scalars(
        select(LineItemRecord)
        .where(LineItemRecord.invoice_id == invoice_id)
        .order_by(LineItemRecord.position)
    ).all()

    def citation(record):
        if record.citation_page is None or record.citation_text is None:
            return None
        return CitationResponse(
            page=record.citation_page,
            source_text=record.citation_text,
            bounding_box=record.bounding_box,
        )

    return ExtractionResponse(
        invoice_id=invoice_id,
        fields=[
            ExtractedFieldResponse(
                name=field.name,
                value=field.value,
                confidence=field.confidence,
                citation=citation(field),
            )
            for field in fields
        ],
        line_items=[
            LineItemResponse(
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.amount,
                citation=citation(item),
            )
            for item in line_items
        ],
        raw_text=extraction.raw_text,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)) -> Invoice:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    return invoice