from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from calendly_bot import book_slot

app = FastAPI()

class BookingRequest(BaseModel):
    name: str
    email: str
    guests: List[str]
    note: str
    month: str
    day: str
    time_str: str

@app.post("/book")
def book(request: BookingRequest):
    try:
        book_slot(
            name=request.name,
            email=request.email,
            guests=request.guests,
            note=request.note,
            month=request.month,
            day=request.day,
            time_str=request.time_str
        )
        return {"status": "success", "message": "Booking attempt completed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
