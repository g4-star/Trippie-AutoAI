from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.routes.auth import get_current_user
from app.services.discovery.discovery_engine import discover_internet_jobs

router = APIRouter(
    prefix="/api/discovery",
    tags=["Internet Discovery"],
)


@router.post("/internet/{user_id}")
def internet_discovery(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden.")

    return discover_internet_jobs(
        db=db,
        user_id=user_id,
        queries_per_cycle=8,
        results_per_query=5,
    )
