from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Joiner(Base):
    __tablename__ = "joiners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    candidate_email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    designation: Mapped[str] = mapped_column(Text, nullable=False)
    team_name: Mapped[str | None] = mapped_column(Text, nullable=True)  # auto-derived from designation
    doj: Mapped[Date] = mapped_column(Date, nullable=False)
    uan: Mapped[str | None] = mapped_column(Text, nullable=True)  # from DB form response, nullable
    current_stage: Mapped[str] = mapped_column(Text, nullable=False, default="NEW")
    sheet_row_index: Mapped[int | None] = mapped_column(Integer, nullable=True)  # row number in HR sheet for back-sync
    hr_notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    bg_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    bg_deadline_date: Mapped[str | None] = mapped_column(Text, nullable=True)  # dd/mm/yyyy, manually entered per send
    bg_deadline_time: Mapped[str | None] = mapped_column(Text, nullable=True)  # e.g. "09:00 AM", manually entered
    bg_received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    offer_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    db_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    db_received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    agreement_signed: Mapped[bool] = mapped_column(Boolean, default=False)
    agreement_signed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    laptop_assigned: Mapped[bool] = mapped_column(Boolean, default=False)
    laptop_assigned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    laptop_asset_tag: Mapped[str | None] = mapped_column(Text, nullable=True)
    sim_required: Mapped[bool] = mapped_column(Boolean, default=False)  # derived from designation
    sim_assigned: Mapped[bool] = mapped_column(Boolean, default=False)
    sim_assigned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    kit_handed_over: Mapped[bool] = mapped_column(Boolean, default=False)
    kit_handed_over_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tshirt_size: Mapped[str | None] = mapped_column(Text, nullable=True)  # S / M / L / XL
    tshirt_handed_over: Mapped[bool] = mapped_column(Boolean, default=False)
    tshirt_handed_over_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    mbti_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    insurance_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    obligation_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    form11_due_date: Mapped[Date | None] = mapped_column(Date, nullable=True)  # computed as doj + 15 days
    form11_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    teams_outlook_done: Mapped[bool] = mapped_column(Boolean, default=False)
    teams_outlook_done_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    znexus_done: Mapped[bool] = mapped_column(Boolean, default=False)
    znexus_done_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    zintlr_tool_done: Mapped[bool] = mapped_column(Boolean, default=False)
    zintlr_tool_done_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scrut_done: Mapped[bool] = mapped_column(Boolean, default=False)
    scrut_done_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    salary_account_discussed: Mapped[bool] = mapped_column(Boolean, default=False)
    salary_account_discussed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    biometric_access_done: Mapped[bool] = mapped_column(Boolean, default=False)
    biometric_access_done_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dropped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dropped_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scheduled_emails: Mapped[list["ScheduledEmail"]] = relationship(back_populates="joiner")
    email_logs: Mapped[list["EmailLog"]] = relationship(back_populates="joiner")
    activity_logs: Mapped[list["ActivityLog"]] = relationship(back_populates="joiner")


# current_stage allowed values (in order):
# NEW, BG_SENT, BG_RECEIVED, OFFER_CONFIRMED, DB_SENT, DB_RECEIVED,
# ONBOARDING, JOINED, FORMS_PENDING, FORM11_DUE, COMPLETED, DROPPED
STAGES = [
    "NEW",
    "BG_SENT",
    "BG_RECEIVED",
    "OFFER_CONFIRMED",
    "DB_SENT",
    "DB_RECEIVED",
    "ONBOARDING",
    "JOINED",
    "FORMS_PENDING",
    "FORM11_DUE",
    "COMPLETED",
    "DROPPED",
]


class ScheduledEmail(Base):
    __tablename__ = "scheduled_emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    joiner_id: Mapped[int] = mapped_column(ForeignKey("joiners.id"), nullable=False)
    email_number: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1 to 4 for pre-onboarding sequence
    template_key: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(Text, default="scheduled")  # scheduled / due / sent / failed / cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    joiner: Mapped["Joiner"] = relationship(back_populates="scheduled_emails")


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_key: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    cc_default: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachments_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    version: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_key: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)  # plain text with Jinja2 variables
    version: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailLog(Base):
    __tablename__ = "email_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    joiner_id: Mapped[int | None] = mapped_column(ForeignKey("joiners.id"), nullable=True)
    template_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    to_addr: Mapped[str | None] = mapped_column(Text, nullable=True)
    cc_addr: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str | None] = mapped_column(Text, nullable=True)  # sent / failed
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)

    joiner: Mapped["Joiner"] = relationship(back_populates="email_logs")


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_type: Mapped[str] = mapped_column(Text, nullable=False)  # kit / tshirt
    size: Mapped[str | None] = mapped_column(Text, nullable=True)  # null for kits, S/M/L/XL/XXL for tshirts
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    threshold: Mapped[int] = mapped_column(Integer, default=3)
    low_stock_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    joiner_id: Mapped[int | None] = mapped_column(ForeignKey("joiners.id"), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str] = mapped_column(Text, default="info")  # info / ok / warn / danger
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    joiner: Mapped["Joiner"] = relationship(back_populates="activity_logs")
