from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from typing import List
import json

from database import get_db
from models import Habit, HabitLog
from schemas import (
    HabitCreate, HabitUpdate, HabitResponse, HabitWithStats,
    HabitLogCreate, HabitLogResponse
)
from auth import get_current_user

router = APIRouter(prefix="/api/habits", tags=["habits"], dependencies=[Depends(get_current_user)])


def calculate_streak(db: Session, habit_id: int) -> int:
    """Calculate the current streak for a habit."""
    today = date.today()
    streak = 0
    current_date = today

    while True:
        log = db.query(HabitLog).filter(
            HabitLog.habit_id == habit_id,
            HabitLog.date == current_date,
            HabitLog.completed == True
        ).first()

        if log:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break

    return streak


def is_scheduled_for_day(habit: Habit, check_date: date) -> bool:
    """Check if habit is scheduled for a specific day."""
    if not habit.schedule_days:
        return True  # No schedule means every day
    
    try:
        days = json.loads(habit.schedule_days)
        if not days:
            return True
        # Python weekday: 0=Monday, 6=Sunday
        return check_date.weekday() in days
    except (json.JSONDecodeError, TypeError):
        return True


def parse_schedule_days(days: List[int] | None) -> str | None:
    """Convert list of days to JSON string for storage."""
    if days is None or len(days) == 0:
        return None
    return json.dumps(days)


def serialize_schedule_days(schedule_days_str: str | None) -> List[int] | None:
    """Convert JSON string to list of days for response."""
    if not schedule_days_str:
        return None
    try:
        return json.loads(schedule_days_str)
    except (json.JSONDecodeError, TypeError):
        return None


@router.get("", response_model=List[HabitWithStats])
def get_habits(include_archived: bool = False, db: Session = Depends(get_db)):
    """Get all active habits with today's stats."""
    today = date.today()
    
    query = db.query(Habit).filter(Habit.is_active == True)
    
    if not include_archived:
        query = query.filter(Habit.is_archived == False)
    
    # Only include habits that have started (start_date is null or <= today)
    from sqlalchemy import or_
    query = query.filter(
        or_(Habit.start_date == None, Habit.start_date <= today)
    )
    
    habits = query.all()

    result = []
    for habit in habits:
        # Get today's log
        log = db.query(HabitLog).filter(
            HabitLog.habit_id == habit.id,
            HabitLog.date == today
        ).first()

        habit_data = HabitWithStats(
            id=habit.id,
            name=habit.name,
            description=habit.description,
            is_repeatable=habit.is_repeatable,
            has_timer=habit.has_timer,
            estimated_duration_seconds=habit.estimated_duration_seconds,
            schedule_days=serialize_schedule_days(habit.schedule_days),
            start_date=habit.start_date,
            is_active=habit.is_active,
            is_archived=habit.is_archived,
            created_at=habit.created_at,
            completed_today=log.completed if log else False,
            time_spent_today=log.time_spent_seconds if log else 0,
            carryover_seconds=log.carryover_seconds if log else 0,
            deficit_seconds=log.deficit_seconds if log else 0,
            streak=calculate_streak(db, habit.id),
            is_scheduled_today=is_scheduled_for_day(habit, today)
        )
        result.append(habit_data)

    return result


@router.post("", response_model=HabitResponse)
def create_habit(habit: HabitCreate, db: Session = Depends(get_db)):
    """Create a new habit."""
    habit_data = habit.model_dump()
    habit_data['schedule_days'] = parse_schedule_days(habit_data.get('schedule_days'))
    
    db_habit = Habit(**habit_data)
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    
    # Return with parsed schedule_days
    response = HabitResponse(
        id=db_habit.id,
        name=db_habit.name,
        description=db_habit.description,
        is_repeatable=db_habit.is_repeatable,
        has_timer=db_habit.has_timer,
        schedule_days=serialize_schedule_days(db_habit.schedule_days),
        is_active=db_habit.is_active,
        is_archived=db_habit.is_archived,
        created_at=db_habit.created_at
    )
    return response


@router.get("/{habit_id}", response_model=HabitWithStats)
def get_habit(habit_id: int, db: Session = Depends(get_db)):
    """Get a specific habit by ID."""
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    today = date.today()
    log = db.query(HabitLog).filter(
        HabitLog.habit_id == habit.id,
        HabitLog.date == today
    ).first()

    return HabitWithStats(
        id=habit.id,
        name=habit.name,
        description=habit.description,
        is_repeatable=habit.is_repeatable,
        has_timer=habit.has_timer,
        schedule_days=serialize_schedule_days(habit.schedule_days),
        is_active=habit.is_active,
        is_archived=habit.is_archived,
        created_at=habit.created_at,
        completed_today=log.completed if log else False,
        time_spent_today=log.time_spent_seconds if log else 0,
        streak=calculate_streak(db, habit.id),
        is_scheduled_today=is_scheduled_for_day(habit, today)
    )


@router.put("/{habit_id}", response_model=HabitResponse)
def update_habit(habit_id: int, habit: HabitUpdate, db: Session = Depends(get_db)):
    """Update a habit."""
    db_habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not db_habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    update_data = habit.model_dump(exclude_unset=True)
    
    # Handle schedule_days conversion
    if 'schedule_days' in update_data:
        update_data['schedule_days'] = parse_schedule_days(update_data['schedule_days'])
    
    for key, value in update_data.items():
        setattr(db_habit, key, value)

    db.commit()
    db.refresh(db_habit)
    
    return HabitResponse(
        id=db_habit.id,
        name=db_habit.name,
        description=db_habit.description,
        is_repeatable=db_habit.is_repeatable,
        has_timer=db_habit.has_timer,
        schedule_days=serialize_schedule_days(db_habit.schedule_days),
        is_active=db_habit.is_active,
        is_archived=db_habit.is_archived,
        created_at=db_habit.created_at
    )


@router.delete("/{habit_id}")
def delete_habit(habit_id: int, db: Session = Depends(get_db)):
    """Delete a habit (soft delete by setting is_active to False)."""
    db_habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not db_habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    db_habit.is_active = False
    db.commit()
    return {"message": "Habit deleted"}


@router.post("/{habit_id}/archive")
def archive_habit(habit_id: int, db: Session = Depends(get_db)):
    """Archive a habit."""
    db_habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not db_habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    db_habit.is_archived = True
    db.commit()
    return {"message": "Habit archived"}


@router.post("/{habit_id}/unarchive")
def unarchive_habit(habit_id: int, db: Session = Depends(get_db)):
    """Unarchive a habit."""
    db_habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not db_habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    db_habit.is_archived = False
    db.commit()
    return {"message": "Habit unarchived"}


@router.post("/{habit_id}/log", response_model=HabitLogResponse)
def log_habit(habit_id: int, log: HabitLogCreate, db: Session = Depends(get_db)):
    """Log habit completion for today."""
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    today = date.today()

    # Check if log already exists for today
    existing_log = db.query(HabitLog).filter(
        HabitLog.habit_id == habit_id,
        HabitLog.date == today
    ).first()

    if existing_log:
        # Update existing log
        existing_log.completed = log.completed
        existing_log.time_spent_seconds = log.time_spent_seconds
        db.commit()
        db.refresh(existing_log)
        return existing_log
    else:
        # Create new log
        db_log = HabitLog(
            habit_id=habit_id,
            date=today,
            completed=log.completed,
            time_spent_seconds=log.time_spent_seconds
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log


@router.get("/{habit_id}/logs", response_model=List[HabitLogResponse])
def get_habit_logs(habit_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Get habit logs for the last N days."""
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    start_date = date.today() - timedelta(days=days)
    logs = db.query(HabitLog).filter(
        HabitLog.habit_id == habit_id,
        HabitLog.date >= start_date
    ).order_by(HabitLog.date.desc()).all()

    return logs


@router.get("/{habit_id}/stats")
def get_habit_stats(habit_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Get detailed statistics for a habit."""
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    start_date = date.today() - timedelta(days=days)
    logs = db.query(HabitLog).filter(
        HabitLog.habit_id == habit_id,
        HabitLog.date >= start_date
    ).all()

    completed_days = sum(1 for log in logs if log.completed)
    total_time = sum(log.time_spent_seconds for log in logs)
    
    return {
        "habit_id": habit_id,
        "habit_name": habit.name,
        "period_days": days,
        "completed_days": completed_days,
        "completion_rate": round((completed_days / days) * 100, 1) if days > 0 else 0,
        "total_time_seconds": total_time,
        "current_streak": calculate_streak(db, habit_id),
        "logs": [
            {
                "date": log.date.isoformat(),
                "completed": log.completed,
                "time_spent_seconds": log.time_spent_seconds
            }
            for log in logs
        ]
    }


@router.get("/by-date/{date_str}")
def get_habits_by_date(date_str: str, db: Session = Depends(get_db)):
    """Get all habits status for a specific date."""
    try:
        check_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    habits = db.query(Habit).filter(Habit.is_active == True, Habit.is_archived == False).all()
    
    result = []
    for habit in habits:
        # Check if habit was scheduled for this day
        scheduled = is_scheduled_for_day(habit, check_date)
        
        # Get log for this date
        log = db.query(HabitLog).filter(
            HabitLog.habit_id == habit.id,
            HabitLog.date == check_date
        ).first()
        
        result.append({
            "habit_id": habit.id,
            "habit_name": habit.name,
            "has_timer": habit.has_timer,
            "estimated_duration_seconds": habit.estimated_duration_seconds,
            "is_scheduled": scheduled,
            "completed": log.completed if log else False,
            "time_spent_seconds": log.time_spent_seconds if log else 0,
            "carryover_seconds": log.carryover_seconds if log else 0,
            "deficit_seconds": log.deficit_seconds if log else 0
        })
    
    return result


@router.put("/by-date/{date_str}/{habit_id}")
def update_habit_log_by_date(
    date_str: str, 
    habit_id: int, 
    completed: bool,
    time_spent_seconds: int = 0,
    db: Session = Depends(get_db)
):
    """Update habit completion for a specific date. Adjusts next day's carryover/deficit if needed."""
    try:
        log_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # Get or create log for this date
    log = db.query(HabitLog).filter(
        HabitLog.habit_id == habit_id,
        HabitLog.date == log_date
    ).first()
    
    if log:
        log.completed = completed
        if time_spent_seconds > 0:
            log.time_spent_seconds = time_spent_seconds
    else:
        log = HabitLog(
            habit_id=habit_id,
            date=log_date,
            completed=completed,
            time_spent_seconds=time_spent_seconds
        )
        db.add(log)
    
    db.flush()
    
    # If it's a timer habit and we're marking as complete, adjust next day's carryover
    if habit.has_timer and habit.estimated_duration_seconds:
        next_date = log_date + timedelta(days=1)
        next_log = db.query(HabitLog).filter(
            HabitLog.habit_id == habit_id,
            HabitLog.date == next_date
        ).first()
        
        if completed:
            # If marking as complete, remove any deficit from next day
            if next_log and next_log.deficit_seconds > 0:
                next_log.deficit_seconds = 0
            
            # If time exceeds estimate, add carryover to next day
            estimated = habit.estimated_duration_seconds
            if log.time_spent_seconds > estimated:
                excess = log.time_spent_seconds - estimated
                if next_log:
                    next_log.carryover_seconds = excess
                else:
                    next_log = HabitLog(
                        habit_id=habit_id,
                        date=next_date,
                        completed=False,
                        time_spent_seconds=0,
                        carryover_seconds=excess
                    )
                    db.add(next_log)
        else:
            # If marking as not complete, calculate deficit for next day
            estimated = habit.estimated_duration_seconds
            deficit = max(0, estimated - log.time_spent_seconds)
            if next_log:
                next_log.deficit_seconds = deficit
                next_log.carryover_seconds = 0
            else:
                next_log = HabitLog(
                    habit_id=habit_id,
                    date=next_date,
                    completed=False,
                    time_spent_seconds=0,
                    deficit_seconds=deficit
                )
                db.add(next_log)
    
    db.commit()
    db.refresh(log)
    
    return {
        "habit_id": habit_id,
        "date": log_date.isoformat(),
        "completed": log.completed,
        "time_spent_seconds": log.time_spent_seconds
    }
