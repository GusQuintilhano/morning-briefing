from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os
from datetime import date

from ..database import get_db
from ..models import BriefingCache

router = APIRouter()

API_KEY = os.getenv("API_KEY", "change-me-in-coolify")

def verify_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

class BriefingUpdate(BaseModel):
    date: Optional[str] = None
    meetings_html: Optional[str] = None
    emails_html: Optional[str] = None
    news_html: Optional[str] = None
    summary_text: Optional[str] = None

def get_latest_briefing(db: Session):
    today = str(date.today())
    return db.query(BriefingCache).filter(BriefingCache.date == today).first()

@router.get("/")
def get_briefing(db: Session = Depends(get_db)):
    today = str(date.today())
    b = db.query(BriefingCache).filter(BriefingCache.date == today).first()
    if not b:
        return {"message": "Nenhum briefing disponível para hoje ainda."}
    return b

@router.post("/", dependencies=[Depends(verify_key)])
def upsert_briefing(data: BriefingUpdate, db: Session = Depends(get_db)):
    target_date = data.date or str(date.today())
    b = db.query(BriefingCache).filter(BriefingCache.date == target_date).first()
    if b:
        for key, value in data.dict(exclude_unset=True).items():
            if key != "date" and value is not None:
                setattr(b, key, value)
    else:
        b = BriefingCache(
            date=target_date,
            meetings_html=data.meetings_html,
            emails_html=data.emails_html,
            news_html=data.news_html,
            summary_text=data.summary_text,
        )
        db.add(b)
    db.commit()
    db.refresh(b)
    return b
