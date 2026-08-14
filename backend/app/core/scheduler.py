from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import EncryptedEvent, Report
from app.core.crypto import add_encrypted_numbers, decrypt_aggregate, get_private_key
import os
import logging

logger = logging.getLogger(__name__)


def run_aggregation():
    """
    The main aggregation job.
    Called every AGGREGATOR_INTERVAL_SECONDS.
    1. Finds all unique event buckets in the database
    2. For each bucket, fetches all ciphertexts
    3. Homomorphically adds them together
    4. Decrypts only the final aggregate
    5. Saves the aggregate to the reports table
    """
    logger.info('Running aggregation job...')
    db: Session = SessionLocal()

    try:
        # Find all distinct bucket names that have events
        buckets = db.query(EncryptedEvent.bucket).distinct().all()
        buckets = [b[0] for b in buckets]

        for bucket in buckets:
            # Fetch all ciphertexts for this bucket
            events = db.query(EncryptedEvent).filter(
                EncryptedEvent.bucket == bucket
            ).all()

            if len(events) < 2:
                # Need at least 2 events for meaningful aggregation
                # With only 1 event the aggregate equals the individual
                logger.info(f'Skipping bucket {bucket}: only {len(events)} event(s)')
                continue

            ciphertext_list = [e.ciphertext for e in events]

            # Homomorphically add all ciphertexts — no individual decryption occurs here
            aggregate_ciphertext = add_encrypted_numbers(ciphertext_list)

            # Decrypt ONLY the final aggregate
            # The private key is used here and only here
            aggregate_value = decrypt_aggregate(aggregate_ciphertext)

            # Save the aggregate report
            report = Report(
                bucket=bucket,
                aggregate_value=float(aggregate_value),
                event_count=len(events)
            )
            db.add(report)
            logger.info(f'Bucket {bucket}: {len(events)} events, aggregate={aggregate_value:.2f}')

        db.commit()
        logger.info('Aggregation job complete.')

    except Exception as e:
        logger.error(f'Aggregation job failed: {e}')
        db.rollback()
        raise
    finally:
        db.close()


def start_scheduler():
    """Creates and starts the APScheduler background scheduler."""
    interval = int(os.getenv('AGGREGATOR_INTERVAL_SECONDS', '600'))
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_aggregation,
        'interval',
        seconds=interval,
        id='aggregation_job',
        name='Privacy-Preserving Aggregator'
    )
    scheduler.start()
    logger.info(f'Aggregator scheduled every {interval} seconds')
    return scheduler