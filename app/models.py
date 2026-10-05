import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    phone_whatsapp: Mapped[str] = mapped_column(String, nullable=False)
    course_interest: Mapped[str] = mapped_column(String, nullable=False)
    preferred_location: Mapped[str] = mapped_column(String, nullable=False)
    current_education: Mapped[str] = mapped_column(String, nullable=False)
    english_test_status: Mapped[str] = mapped_column(String, nullable=False)
    budget_intake: Mapped[str] = mapped_column(String, nullable=False)
    budget: Mapped[str | None] = mapped_column(String, nullable=True)
    intake: Mapped[str | None] = mapped_column(String, nullable=True)
    current_country_status: Mapped[str] = mapped_column(String, nullable=False)
    lead_status: Mapped[str] = mapped_column(
        String, nullable=False, default="LOW_INTENT"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
