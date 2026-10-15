import os

from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401
from app.models.job_email_draft import JobEmailDraft  # noqa: F401
from app.models.gmail_draft_authorization import GmailDraftAuthorization  # noqa: F401
from app.models.gmail_oauth_transaction import GmailOAuthTransaction  # noqa: F401
from app.routes.auth import router as auth_router
from app.routes.documents import router as documents_router
from app.routes.profile import router as profile_router
from app.routes.jobs import router as jobs_router
from app.routes.applications import router as applications_router
from app.routes.dashboard import router as dashboard_router
from app.routes.emails import router as emails_router
from app.routes.gmail import router as gmail_router
from app.routes.settings import router as settings_router
from app.routes.agent import router as agent_router
from app.routes.internet_discovery import router as internet_discovery_router
from app.routes.job_drafts import router as job_drafts_router
from app.routes.cron import router as cron_router
from app.services.agent_worker import start_agent_worker, stop_agent_worker

app = FastAPI(
    title=settings.app_name,
    description="Personal AI-powered job application assistant",
    version="0.2.0",
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    if os.getenv("ENABLE_BACKGROUND_WORKER", "false").strip().lower() in {"1", "true", "yes", "on"}:
        start_agent_worker()


@app.on_event("shutdown")
def shutdown():
    stop_agent_worker()


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "version": "0.2.0",
        "job_email_drafts": "enabled" if os.getenv("AUTO_DRAFT_JOB_EMAILS", "true").lower() not in {"0", "false", "no", "off"} else "disabled",
        "worker_enabled": os.getenv("ENABLE_BACKGROUND_WORKER", "false").lower() in {"1", "true", "yes", "on"},
    }


@app.get("/api/health")
def health():
    return {"status": "healthy", "database": "connected"}


app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(profile_router)
app.include_router(jobs_router)
app.include_router(applications_router)
app.include_router(dashboard_router)
app.include_router(emails_router)
app.include_router(gmail_router)
app.include_router(settings_router)
app.include_router(agent_router)
app.include_router(internet_discovery_router)
app.include_router(job_drafts_router)
app.include_router(cron_router)
