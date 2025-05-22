from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List
from calendly_bot import book_slot

app = FastAPI()

class BookingRequest(BaseModel):
    name: str
    email: EmailStr
    guests: List[EmailStr] = []
    note: str = ""
    month: str
    day: str
    time: str

@app.post("/book")
def book_appointment(payload: BookingRequest):
    try:
        book_slot(
            name=payload.name,
            email=payload.email,
            guests=payload.guests,
            note=payload.note,
            month=payload.month,
            day=payload.day,
            time_str=payload.time
        )
        return {"status": "success", "message": "Booking attempted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
