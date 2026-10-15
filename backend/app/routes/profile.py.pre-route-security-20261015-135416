from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.auth import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/api/profile",
    tags=["Profile"],
)


class ProfileCreate(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    bio: str | None = None
    skills: str | None = None
    preferred_categories: str | None = None
    preferred_locations: str | None = None
    work_preference: str = "remote_or_onsite"
    experience_level: str = "entry_level"
    minimum_salary: int | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    bio: str | None = None
    skills: str | None = None
    preferred_categories: str | None = None
    preferred_locations: str | None = None
    work_preference: str | None = None
    experience_level: str | None = None
    minimum_salary: int | None = None


def profile_response(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "bio": user.bio,
        "skills": user.skills,
        "preferred_categories": user.preferred_categories,
        "preferred_locations": user.preferred_locations,
        "work_preference": user.work_preference,
        "experience_level": user.experience_level,
        "minimum_salary": user.minimum_salary,
        "is_active": user.is_active,
    }


@router.post("")
def create_profile():
    raise HTTPException(
        status_code=410,
        detail="Public profile creation is disabled. Use /api/auth/register.",
    )

@router.get("/{user_id}")
def get_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden.")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Profile not found.",
        )

    return profile_response(user)


@router.put("/{user_id}")
def update_profile(
    user_id: int,
    profile: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden.")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Profile not found.",
        )

    updates = profile.model_dump(exclude_unset=True)

    if "email" in updates:
        existing = (
            db.query(User)
            .filter(
                User.email == updates["email"],
                User.id != user_id,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Another profile already uses this email.",
            )

    for field, value in updates.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return profile_response(user)
