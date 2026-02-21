from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from typing import List

from database import get_db
from models import Habit, HabitLog, Note, TimerSession
from schemas import DashboardStats, DailyProgress
from auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    today = date.today()

    # Total active habits
    total_habits = db.query(Habit).filter(Habit.is_active == True).count()

    # Completed today
    completed_today = db.query(HabitLog).filter(
        HabitLog.date == today,
        HabitLog.completed == True
    ).count()

    # Completion percentage (capped at 100%)
    completion_percentage = min((completed_today / total_habits * 100), 100) if total_habits > 0 else 0

    # Total time today (from timer sessions)
    total_time = db.query(func.sum(TimerSession.duration_seconds)).filter(
        TimerSession.date == today,
        TimerSession.is_running == False
    ).scalar() or 0

    # Calculate current streak (consecutive days with all habits completed)
    current_streak = 0
    check_date = today

    while True:
        day_completed = db.query(HabitLog).filter(
            HabitLog.date == check_date,
            HabitLog.completed == True
        ).count()

        day_total = db.query(Habit).filter(
            Habit.is_active == True
        ).count()

        if day_total > 0 and day_completed >= day_total:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # Notes today
    notes_today = db.query(Note).filter(Note.date == today).count()

    return DashboardStats(
        total_habits=total_habits,
        completed_today=completed_today,
        completion_percentage=round(completion_percentage, 1),
        total_time_today=total_time,
        current_streak=current_streak,
        notes_today=notes_today
    )


@router.get("/progress", response_model=List[DailyProgress])
def get_daily_progress(days: int = 7, db: Session = Depends(get_db)):
    """Get daily progress for the last N days."""
    today = date.today()
    result = []

    for i in range(days):
        check_date = today - timedelta(days=i)

        # Get total active habits on this day
        total = db.query(Habit).filter(
            Habit.is_active == True
        ).count()

        # Get completed habits on this day
        completed = db.query(HabitLog).filter(
            HabitLog.date == check_date,
            HabitLog.completed == True
        ).count()

        percentage = min((completed / total * 100), 100) if total > 0 else 0

        result.append(DailyProgress(
            date=check_date,
            completed=completed,
            total=total,
            percentage=round(percentage, 1)
        ))

    return list(reversed(result))
