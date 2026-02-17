from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers import habits, notes, timers, dashboard, settings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Eye Life API",
    description="API for daily life tracking - habits, notes, and timers",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(habits.router)
app.include_router(notes.router)
app.include_router(timers.router)
app.include_router(dashboard.router)
app.include_router(settings.router)


@app.get("/")
def root():
    return {"message": "Eye Life API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
