from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine

# Import all models so SQLAlchemy knows about every table.
from app import models  # noqa: F401
from app.routes.profile import router as profile_router
from app.routes.jobs import router as jobs_router
from app.routes.applications import router as applications_router
from app.routes.dashboard import router as dashboard_router
from app.routes.emails import router as emails_router
from app.routes.gmail import router as gmail_router
from app.routes.settings import router as settings_router
from app.routes.agent import router as agent_router
from app.services.agent_worker import start_agent_worker


app = FastAPI(
    title=settings.app_name,
    description="Personal AI-powered job application assistant",
    version="0.1.0",
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    start_agent_worker()


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "database": "connected",
    }

app.include_router(profile_router)
app.include_router(jobs_router)
app.include_router(applications_router)
app.include_router(dashboard_router)
app.include_router(emails_router)
app.include_router(gmail_router)
app.include_router(settings_router)
app.include_router(agent_router)
