from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.db.database import get_db
from app.db.models import EncryptedEvent, Report
from app.core.crypto import get_public_key
from app.core.scheduler import run_aggregation
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Pydantic schemas (data shapes for incoming requests) ──────────────────

class EventSubmission(BaseModel):
    """The shape of data the client SDK sends to /analytics/event"""
    bucket: str          # e.g. 'video_complete' or 'feature_click'
    ciphertext: str      # The encrypted integer, as a large string


class ReportResponse(BaseModel):
    """The shape of data returned from /analytics/reports"""
    bucket: str
    aggregate_value: float
    event_count: int
    created_at: str


# ── Routes ────────────────────────────────────────────────────────────────

@router.get('/analytics/pubkey')
def get_public_key_endpoint():
    """
    Returns the Paillier public key.
    Clients need this to encrypt their data before sending it.
    The public key is not secret — it is safe to expose publicly.
    """
    pub = get_public_key()
    # The only field clients need is 'n', the public modulus
    return {'n': str(pub.n)}


@router.post('/analytics/event', status_code=201)
def submit_event(event: EventSubmission, db: Session = Depends(get_db)):
    """
    Receives an encrypted event from a client.
    Stores only the ciphertext and the bucket name.
    No user data, no IP addresses, nothing identifying.
    """
    # Basic validation: bucket name must be alphanumeric with underscores
    if not event.bucket.replace('_', '').isalnum():
        raise HTTPException(status_code=400, detail='Invalid bucket name')

    # Validate that ciphertext is a valid large integer string
    try:
        int(event.ciphertext)
    except ValueError:
        raise HTTPException(status_code=400, detail='Ciphertext must be an integer string')

    db_event = EncryptedEvent(
        bucket=event.bucket,
        ciphertext=event.ciphertext
    )
    db.add(db_event)
    db.commit()
    logger.info(f'Event stored for bucket: {event.bucket}')
    return {'status': 'ok'}


@router.get('/analytics/reports')
def get_reports(bucket: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Returns the most recent aggregation report for each bucket.
    Optionally filter by a specific bucket name.
    Only aggregate values are returned — no individual event data.
    """
    query = db.query(Report)
    if bucket:
        query = query.filter(Report.bucket == bucket)
    reports = query.order_by(Report.created_at.desc()).limit(50).all()

    return [
        {
            'bucket': r.bucket,
            'aggregate_value': r.aggregate_value,
            'event_count': r.event_count,
            'created_at': r.created_at.isoformat() if r.created_at else None
        }
        for r in reports
    ]


@router.post('/analytics/aggregate/run', status_code=200)
def trigger_aggregation():
    """
    Manually trigger the aggregation job.
    Useful for testing without waiting 10 minutes.
    In production you would protect this endpoint with an admin token.
    """
    try:
        run_aggregation()
        return {'status': 'aggregation complete'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/health')
def health_check():
    """Simple health check endpoint for Docker and load balancers."""
    return {'status': 'healthy'}