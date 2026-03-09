from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from .database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    done = Column(Boolean, default=False)
    priority = Column(String, default="normal")  # low, normal, high
    due_date = Column(String, nullable=True)      # ISO date string "2026-03-08"
    created_at = Column(DateTime, server_default=func.now())

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=True)
    due_date = Column(String, nullable=True)      # ISO date string
    paid = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class BriefingCache(Base):
    __tablename__ = "briefing_cache"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False, unique=True)  # "2026-03-08"
    meetings_html = Column(Text, nullable=True)
    emails_html = Column(Text, nullable=True)
    news_html = Column(Text, nullable=True)
    summary_text = Column(Text, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
