from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import AppSettings, Habit, HabitLog, Note, TimerSession
from schemas import SettingsResponse, SettingsUpdate
from auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"], dependencies=[Depends(get_current_user)])


def get_setting(db: Session, key: str, default: str = "") -> str:
    """Get a setting value by key."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    return setting.value if setting else default


def set_setting(db: Session, key: str, value: str):
    """Set a setting value by key."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = AppSettings(key=key, value=value)
        db.add(setting)
    db.commit()


@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """Get all application settings."""
    carryover_value = get_setting(db, "carryover_enabled", "false")
    return SettingsResponse(
        carryover_enabled=carryover_value.lower() == "true"
    )


@router.put("", response_model=SettingsResponse)
def update_settings(settings: SettingsUpdate, db: Session = Depends(get_db)):
    """Update application settings."""
    if settings.carryover_enabled is not None:
        set_setting(db, "carryover_enabled", str(settings.carryover_enabled).lower())
    
    return get_settings(db)


@router.delete("/reset-all")
def reset_all_data(db: Session = Depends(get_db)):
    """Delete ALL user data: habits, logs, notes, timer sessions, and settings."""
    # Delete in correct order (children first due to foreign keys)
    db.query(TimerSession).delete()
    db.query(HabitLog).delete()
    db.query(Habit).delete()
    db.query(Note).delete()
    db.query(AppSettings).delete()
    db.commit()
    return {"message": "Todos os dados foram apagados com sucesso."}

