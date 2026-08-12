from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from app.db.database import Base

class EncryptedEvent(Base):
    """
    One row per analytics event submitted by a client.
    We store ONLY the encrypted ciphertext. No user ID.
    No IP address. No session. Nothing that identifies the user.
    """
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, index=True)

    # The event type, e.g. 'video_complete', 'feature_click', 'session_start'
    bucket = Column(String(100), nullable=False, index=True)

    # The encrypted value, serialised as a long string
    # We use Text (unlimited length) because Paillier ciphertexts are very large numbers
    ciphertext = Column(Text, nullable=False)

    # When the event was received
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    """
    One row per aggregation run per bucket.
    This table contains ONLY population-level aggregate values.
    Individual events are never stored here.
    """
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True, index=True)
    bucket = Column(String(100), nullable=False, index=True)

    # The decrypted aggregate value (total sum across all users in this bucket)
    aggregate_value = Column(Float, nullable=False)

    # How many encrypted events were included in this aggregate
    event_count = Column(Integer, nullable=False)

    # When this report was generated
    created_at = Column(DateTime(timezone=True), server_default=func.now())