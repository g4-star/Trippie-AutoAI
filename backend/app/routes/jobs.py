from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.services.discovery.discovery_engine import discover_internet_jobs
from app.services.job_matcher import match_jobs_for_user


router = APIRouter(
    prefix="/api/jobs",
    tags=["Jobs"],
)


@router.get("")
def get_jobs(
    db: Session = Depends(get_db),
):
    jobs = db.scalars(
        select(Job)
        .where(Job.is_active.is_(True))
        .order_by(Job.discovered_at.desc())
    ).all()

    return {
        "count": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "external_id": job.external_id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "description": job.description,
                "requirements": job.requirements,
                "job_url": job.job_url,
                "source": job.source,
                "employment_type": job.employment_type,
                "salary": job.salary,
                "match_score": job.match_score,
                "is_active": job.is_active,
                "discovered_at": job.discovered_at,
                "updated_at": job.updated_at,
            }
            for job in jobs
        ],
    }


@router.post("/match/{user_id}")
def match_jobs_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
):
    return match_jobs_for_user(
        db=db,
        user_id=user_id,
    )


@router.get("/{job_id}")
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)

    if not job:
        return {
            "detail": "Job not found.",
        }

    return {
        "id": job.id,
        "external_id": job.external_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "requirements": job.requirements,
        "job_url": job.job_url,
        "source": job.source,
        "employment_type": job.employment_type,
        "salary": job.salary,
        "match_score": job.match_score,
        "is_active": job.is_active,
        "discovered_at": job.discovered_at,
        "updated_at": job.updated_at,
    }


@router.post("/discover")
def discover_jobs_endpoint(
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    return discover_internet_jobs(
        db=db,
        user_id=user_id,
    )
