from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List


# ==================== Habit Schemas ====================

class HabitBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_repeatable: bool = True
    has_timer: bool = False
    # Estimated duration for timed habits (in seconds), null = no limit
    estimated_duration_seconds: Optional[int] = None
    # List of weekday numbers (0=Monday, 6=Sunday), null/empty means every day
    schedule_days: Optional[List[int]] = None
    # Start date for the habit (when it becomes active)
    start_date: Optional[date] = None


class HabitCreate(HabitBase):
    pass


class HabitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_repeatable: Optional[bool] = None
    has_timer: Optional[bool] = None
    estimated_duration_seconds: Optional[int] = None
    schedule_days: Optional[List[int]] = None
    start_date: Optional[date] = None
    is_active: Optional[bool] = None
    is_archived: Optional[bool] = None


class HabitResponse(HabitBase):
    id: int
    is_active: bool
    is_archived: bool = False
    start_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HabitWithStats(HabitResponse):
    completed_today: bool = False
    time_spent_today: int = 0
    carryover_seconds: int = 0
    deficit_seconds: int = 0
    streak: int = 0
    is_scheduled_today: bool = True


# ==================== Habit Log Schemas ====================

class HabitLogCreate(BaseModel):
    completed: bool = True
    time_spent_seconds: int = 0


class HabitLogResponse(BaseModel):
    id: int
    habit_id: int
    date: date
    completed: bool
    time_spent_seconds: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Note Schemas ====================

class NoteBase(BaseModel):
    content: str
    date: date


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    content: Optional[str] = None
    date: Optional[date] = None


class NoteResponse(NoteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotesByDate(BaseModel):
    date: date
    notes: List[NoteResponse]


# ==================== Timer Schemas ====================

class TimerStart(BaseModel):
    habit_id: int


class TimerStop(BaseModel):
    habit_id: int


class TimerResponse(BaseModel):
    id: int
    habit_id: int
    date: date
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: int
    is_running: bool

    class Config:
        from_attributes = True


class TimerStatus(BaseModel):
    is_running: bool
    current_session: Optional[TimerResponse] = None
    total_time_today: int = 0


# ==================== Dashboard Schemas ====================

class DashboardStats(BaseModel):
    total_habits: int
    completed_today: int
    completion_percentage: float
    total_time_today: int
    current_streak: int
    notes_today: int


class DailyProgress(BaseModel):
    date: date
    completed: int
    total: int
    percentage: float


# ==================== Settings Schemas ====================

class SettingsResponse(BaseModel):
    carryover_enabled: bool = False


class SettingsUpdate(BaseModel):
    carryover_enabled: Optional[bool] = None
