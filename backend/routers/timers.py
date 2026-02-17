from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
from typing import Optional

from database import get_db
from models import Habit, HabitLog, TimerSession, AppSettings
from schemas import TimerStart, TimerStop, TimerResponse, TimerStatus
from auth import get_current_user

router = APIRouter(prefix="/api/timers", tags=["timers"], dependencies=[Depends(get_current_user)])


def get_setting(db: Session, key: str, default: str = "") -> str:
    """Get a setting value by key."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    return setting.value if setting else default


@router.post("/start", response_model=TimerResponse)
def start_timer(timer: TimerStart, db: Session = Depends(get_db)):
    """Start a timer for a habit."""
    habit = db.query(Habit).filter(Habit.id == timer.habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    if not habit.has_timer:
        raise HTTPException(status_code=400, detail="This habit does not have timer enabled")

    # Check if there's already a running timer for this habit and stop it
    running = db.query(TimerSession).filter(
        TimerSession.habit_id == timer.habit_id,
        TimerSession.is_running == True
    ).first()

    if running:
        # Stop the existing timer before starting a new one
        now = datetime.utcnow()
        running.end_time = now
        running.duration_seconds = int((now - running.start_time).total_seconds())
        running.is_running = False
        db.flush()

    # Create new timer session
    today = date.today()
    now = datetime.utcnow()

    session = TimerSession(
        habit_id=timer.habit_id,
        date=today,
        start_time=now,
        is_running=True
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return session


@router.post("/stop", response_model=TimerResponse)
def stop_timer(timer: TimerStop, db: Session = Depends(get_db)):
    """Stop the running timer for a habit."""
    # Find running timer
    session = db.query(TimerSession).filter(
        TimerSession.habit_id == timer.habit_id,
        TimerSession.is_running == True
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="No running timer found for this habit")

    # Get habit info for carryover calculation
    habit = db.query(Habit).filter(Habit.id == timer.habit_id).first()

    # Stop timer and calculate duration
    now = datetime.utcnow()
    session.end_time = now
    session.duration_seconds = int((now - session.start_time).total_seconds())
    session.is_running = False

    # Update habit log with time spent
    today = date.today()
    log = db.query(HabitLog).filter(
        HabitLog.habit_id == timer.habit_id,
        HabitLog.date == today
    ).first()

    if log:
        log.time_spent_seconds += session.duration_seconds
    else:
        log = HabitLog(
            habit_id=timer.habit_id,
            date=today,
            completed=False,
            time_spent_seconds=session.duration_seconds
        )
        db.add(log)
    
    db.flush()  # Ensure log is saved before carryover/deficit calculation

    # Check for carryover/deficit logic
    carryover_enabled = get_setting(db, "carryover_enabled", "false").lower() == "true"
    
    if carryover_enabled and habit and habit.estimated_duration_seconds:
        estimated = habit.estimated_duration_seconds
        time_spent = log.time_spent_seconds
        
        # Get yesterday's log to check for deficit
        yesterday = today - timedelta(days=1)
        yesterday_log = db.query(HabitLog).filter(
            HabitLog.habit_id == timer.habit_id,
            HabitLog.date == yesterday
        ).first()
        
        # Check if today's time fulfills yesterday's deficit (retroactive completion)
        if yesterday_log and not yesterday_log.completed and yesterday_log.deficit_seconds > 0:
            # Check if today's time + yesterday's time >= estimated
            total_time = yesterday_log.time_spent_seconds + time_spent
            if total_time >= estimated:
                # Mark yesterday as completed!
                yesterday_log.completed = True
                yesterday_log.deficit_seconds = 0
        
        # Calculate today's status
        if time_spent >= estimated:
            # Time spent exceeds or meets estimated - carry over excess
            if time_spent > estimated:
                excess = time_spent - estimated
                
                # Get or create next day's log
                tomorrow = today + timedelta(days=1)
                next_log = db.query(HabitLog).filter(
                    HabitLog.habit_id == timer.habit_id,
                    HabitLog.date == tomorrow
                ).first()
                
                if next_log:
                    next_log.carryover_seconds = excess
                else:
                    next_log = HabitLog(
                        habit_id=timer.habit_id,
                        date=tomorrow,
                        completed=False,
                        time_spent_seconds=0,
                        carryover_seconds=excess
                    )
                    db.add(next_log)
        else:
            # Time spent is less than estimated - calculate deficit for next day
            deficit = estimated - time_spent
            
            # Get or create next day's log
            tomorrow = today + timedelta(days=1)
            next_log = db.query(HabitLog).filter(
                HabitLog.habit_id == timer.habit_id,
                HabitLog.date == tomorrow
            ).first()
            
            if next_log:
                next_log.deficit_seconds = deficit
            else:
                next_log = HabitLog(
                    habit_id=timer.habit_id,
                    date=tomorrow,
                    completed=False,
                    time_spent_seconds=0,
                    deficit_seconds=deficit
                )
                db.add(next_log)

    db.commit()
    db.refresh(session)

    return session


@router.get("/{habit_id}/status", response_model=TimerStatus)
def get_timer_status(habit_id: int, db: Session = Depends(get_db)):
    """Get timer status for a habit."""
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    # Get running timer
    running = db.query(TimerSession).filter(
        TimerSession.habit_id == habit_id,
        TimerSession.is_running == True
    ).first()

    # Calculate total time today
    today = date.today()
    total_time = db.query(func.sum(TimerSession.duration_seconds)).filter(
        TimerSession.habit_id == habit_id,
        TimerSession.date == today,
        TimerSession.is_running == False
    ).scalar() or 0

    # Add current session time if running
    current_session = None
    if running:
        current_duration = int((datetime.utcnow() - running.start_time).total_seconds())
        total_time += current_duration
        current_session = TimerResponse(
            id=running.id,
            habit_id=running.habit_id,
            date=running.date,
            start_time=running.start_time,
            end_time=running.end_time,
            duration_seconds=current_duration,
            is_running=True
        )

    return TimerStatus(
        is_running=running is not None,
        current_session=current_session,
        total_time_today=total_time
    )


@router.get("/{habit_id}/today")
def get_today_time(habit_id: int, db: Session = Depends(get_db)):
    """Get total time spent on a habit today."""
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    today = date.today()
    total_time = db.query(func.sum(TimerSession.duration_seconds)).filter(
        TimerSession.habit_id == habit_id,
        TimerSession.date == today,
        TimerSession.is_running == False
    ).scalar() or 0

    # Check for running timer
    running = db.query(TimerSession).filter(
        TimerSession.habit_id == habit_id,
        TimerSession.is_running == True
    ).first()

    if running:
        current_duration = int((datetime.utcnow() - running.start_time).total_seconds())
        total_time += current_duration

    return {"habit_id": habit_id, "total_seconds": total_time}


@router.post("/{habit_id}/reset")
def reset_timer(habit_id: int, db: Session = Depends(get_db)):
    """Reset all time spent on a habit today and restart timer if running."""
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    today = date.today()
    now = datetime.utcnow()

    # Check for running timer
    running = db.query(TimerSession).filter(
        TimerSession.habit_id == habit_id,
        TimerSession.is_running == True
    ).first()
    
    # Delete all completed timer sessions for today
    db.query(TimerSession).filter(
        TimerSession.habit_id == habit_id,
        TimerSession.date == today,
        TimerSession.is_running == False
    ).delete()
    
    # If there's a running timer, restart it from now
    if running:
        running.start_time = now
        running.duration_seconds = 0
    
    # Reset time in habit log
    log = db.query(HabitLog).filter(
        HabitLog.habit_id == habit_id,
        HabitLog.date == today
    ).first()
    
    if log:
        log.time_spent_seconds = 0
    
    db.commit()

    return {"message": "Timer reset successfully", "habit_id": habit_id}

