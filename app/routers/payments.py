from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os

from ..database import get_db
from ..models import Payment

router = APIRouter()

API_KEY = os.getenv("API_KEY", "change-me-in-coolify")

def verify_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

class PaymentCreate(BaseModel):
    title: str
    amount: Optional[float] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None

class PaymentUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    due_date: Optional[str] = None
    paid: Optional[bool] = None
    notes: Optional[str] = None

def get_payments_db(db: Session):
    return db.query(Payment).filter(Payment.paid == False).order_by(Payment.due_date).all()

@router.get("/")
def list_payments(db: Session = Depends(get_db)):
    return db.query(Payment).order_by(Payment.due_date).all()

@router.post("/", dependencies=[Depends(verify_key)])
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    db_payment = Payment(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

@router.put("/{payment_id}", dependencies=[Depends(verify_key)])
def update_payment(payment_id: int, payment: PaymentUpdate, db: Session = Depends(get_db)):
    db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    for key, value in payment.dict(exclude_unset=True).items():
        setattr(db_payment, key, value)
    db.commit()
    db.refresh(db_payment)
    return db_payment

@router.delete("/{payment_id}", dependencies=[Depends(verify_key)])
def delete_payment(payment_id: int, payment: PaymentUpdate, db: Session = Depends(get_db)):
    db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    db.delete(db_payment)
    db.commit()
    return {"ok": True}
