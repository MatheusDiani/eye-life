from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_repeatable = Column(Boolean, default=True)
    has_timer = Column(Boolean, default=False)
    # Estimated time to spend on this habit daily (in seconds), null = no limit
    estimated_duration_seconds = Column(Integer, nullable=True)
    # JSON string: list of weekday numbers (0=Monday, 6=Sunday), null means every day
    schedule_days = Column(String(50), nullable=True)
    # Date when this habit starts (habits are not shown before this date)
    start_date = Column(Date, nullable=True)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    logs = relationship("HabitLog", back_populates="habit", cascade="all, delete-orphan")
    timer_sessions = relationship("TimerSession", back_populates="habit", cascade="all, delete-orphan")


class HabitLog(Base):
    __tablename__ = "habit_logs"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False)
    time_spent_seconds = Column(Integer, default=0)
    # Time carried over from previous day (excess time - bonus)
    carryover_seconds = Column(Integer, default=0)
    # Time deficit from previous day (remaining time that was not completed)
    deficit_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    habit = relationship("Habit", back_populates="logs")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TimerSession(Base):
    __tablename__ = "timer_sessions"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    is_running = Column(Boolean, default=True)

    habit = relationship("Habit", back_populates="timer_sessions")


class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(255), nullable=True)
