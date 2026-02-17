from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List, Optional

from database import get_db
from models import Note
from schemas import NoteCreate, NoteUpdate, NoteResponse, NotesByDate
from auth import get_current_user

router = APIRouter(prefix="/api/notes", tags=["notes"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=List[NoteResponse])
def get_notes(
    note_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get notes, optionally filtered by date."""
    query = db.query(Note)

    if note_date:
        query = query.filter(Note.date == note_date)

    notes = query.order_by(Note.date.desc(), Note.created_at.desc()).all()
    return notes


@router.get("/today", response_model=List[NoteResponse])
def get_today_notes(db: Session = Depends(get_db)):
    """Get today's notes."""
    today = date.today()
    notes = db.query(Note).filter(Note.date == today).order_by(Note.created_at.desc()).all()
    return notes


@router.get("/by-date", response_model=List[NotesByDate])
def get_notes_grouped_by_date(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get all notes grouped by date (for the history view)."""
    query = db.query(Note)

    if start_date:
        query = query.filter(Note.date >= start_date)
    if end_date:
        query = query.filter(Note.date <= end_date)

    notes = query.order_by(Note.date.desc(), Note.created_at.desc()).all()

    # Group notes by date
    notes_by_date = {}
    for note in notes:
        if note.date not in notes_by_date:
            notes_by_date[note.date] = []
        notes_by_date[note.date].append(note)

    # Convert to list of NotesByDate
    result = [
        NotesByDate(date=d, notes=notes_list)
        for d, notes_list in sorted(notes_by_date.items(), reverse=True)
    ]

    return result


@router.post("", response_model=NoteResponse)
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    """Create a new note."""
    db_note = Note(**note.model_dump())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db)):
    """Get a specific note by ID."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.put("/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, note: NoteUpdate, db: Session = Depends(get_db)):
    """Update a note."""
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")

    update_data = note.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_note, key, value)

    db.commit()
    db.refresh(db_note)
    return db_note


@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note."""
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(db_note)
    db.commit()
    return {"message": "Note deleted"}
