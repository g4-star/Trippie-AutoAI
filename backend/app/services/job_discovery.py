from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.services.sources.brighter_monday import discover_jobs


def save_discovered_job(db: Session, job_data: dict) -> tuple[Job, bool]:
    """
    Save one normalized job.

    Returns:
        (job, created)

    created=True  -> new job inserted
    created=False -> existing job updated
    """

    external_id = job_data.get("external_id")

    if not external_id:
        raise ValueError("Job is missing external_id")

    existing = db.scalar(
        select(Job).where(Job.external_id == external_id)
    )

    if existing:
        for field in [
            "title",
            "company",
            "location",
            "description",
            "requirements",
            "experience_requirements",
            "education_requirements",
            "date_posted",
            "valid_through",
            "job_url",
            "source",
            "employment_type",
            "salary",
        ]:
            if field in job_data:
                setattr(existing, field, job_data[field])

        db.commit()
        db.refresh(existing)

        return existing, False

    job = Job(
        external_id=external_id,
        title=job_data["title"],
        company=job_data["company"] or "Unknown",
        location=job_data.get("location"),
        description=job_data.get("description"),
        requirements=job_data.get("requirements"),
        experience_requirements=job_data.get("experience_requirements"),
        education_requirements=job_data.get("education_requirements"),
        date_posted=job_data.get("date_posted"),
        valid_through=job_data.get("valid_through"),
        job_url=job_data.get("job_url"),
        source=job_data.get("source"),
        employment_type=job_data.get("employment_type"),
        salary=job_data.get("salary"),
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job, True


def discover_and_save_jobs(
    db: Session,
    limit: int = 20,
) -> dict:
    """
    Discover jobs from supported sources and save them to the database.
    """

    discovered = discover_jobs(limit=limit)

    created = 0
    updated = 0
    failed = 0

    saved_jobs = []

    for job_data in discovered:
        try:
            job, was_created = save_discovered_job(
                db,
                job_data,
            )

            if was_created:
                created += 1
            else:
                updated += 1

            saved_jobs.append(
                {
                    "id": job.id,
                    "external_id": job.external_id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "source": job.source,
                }
            )

        except Exception:
            db.rollback()
            failed += 1

    return {
        "discovered": len(discovered),
        "created": created,
        "updated": updated,
        "failed": failed,
        "jobs": saved_jobs,
    }
