from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text
from pydantic import BaseModel
from typing import Optional
import os, json

from ..database import get_db, Base
from ..models import Task, Payment

router = APIRouter()

API_KEY = os.getenv("API_KEY", "change-me-in-coolify")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_EMAIL = os.getenv("VAPID_EMAIL", "mailto:gus.quintilhano@gmail.com")

def verify_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# Model for push subscription storage
class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    id = Column(Integer, primary_key=True)
    endpoint = Column(String, unique=True)
    p256dh = Column(String)
    auth = Column(String)

class SubscriptionData(BaseModel):
    endpoint: str
    p256dh: str
    auth: str

class PushPayload(BaseModel):
    title: str
    body: str
    icon: Optional[str] = "/static/icon.png"

@router.get("/vapid-public-key")
def get_public_key():
    return {"publicKey": VAPID_PUBLIC_KEY}

@router.post("/subscribe")
def subscribe(data: SubscriptionData, db: Session = Depends(get_db)):
    """Register browser for push notifications."""
    existing = db.query(PushSubscription).filter(
        PushSubscription.endpoint == data.endpoint
    ).first()
    if existing:
        existing.p256dh = data.p256dh
        existing.auth = data.auth
    else:
        sub = PushSubscription(endpoint=data.endpoint, p256dh=data.p256dh, auth=data.auth)
        db.add(sub)
    db.commit()
    return {"ok": True}

@router.post("/send", dependencies=[Depends(verify_key)])
def send_push(payload: PushPayload, db: Session = Depends(get_db)):
    """Send a push notification to all registered browsers."""
    if not VAPID_PRIVATE_KEY:
        raise HTTPException(status_code=503, detail="Push not configured (missing VAPID keys)")

    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        raise HTTPException(status_code=503, detail="pywebpush not installed")

    subs = db.query(PushSubscription).all()
    results = []
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth}
                },
                data=json.dumps({"title": payload.title, "body": payload.body}),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_EMAIL}
            )
            results.append({"endpoint": sub.endpoint[:40], "status": "sent"})
        except Exception as e:
            results.append({"endpoint": sub.endpoint[:40], "status": "error", "detail": str(e)})
    return {"results": results}

@router.get("/check-due")
def check_due_today(db: Session = Depends(get_db)):
    """Returns tasks and payments due today — used by the skill to decide whether to push."""
    from datetime import date
    today = str(date.today())
    tasks_due = db.query(Task).filter(Task.due_date == today, Task.done == False).all()
    payments_due = db.query(Payment).filter(Payment.due_date == today, Payment.paid == False).all()
    return {
        "tasks": [{"id": t.id, "title": t.title} for t in tasks_due],
        "payments": [{"id": p.id, "title": p.title, "amount": p.amount} for p in payments_due],
    }
