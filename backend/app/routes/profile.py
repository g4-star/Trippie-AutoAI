from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
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
def create_profile(
    profile: ProfileCreate,
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == profile.email).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="A profile with this email already exists.",
        )

    user = User(
        full_name=profile.full_name,
        email=profile.email,
        phone=profile.phone,
        bio=profile.bio,
        skills=profile.skills,
        preferred_categories=profile.preferred_categories,
        preferred_locations=profile.preferred_locations,
        work_preference=profile.work_preference,
        experience_level=profile.experience_level,
        minimum_salary=profile.minimum_salary,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return profile_response(user)


@router.get("/{user_id}")
def get_profile(
    user_id: int,
    db: Session = Depends(get_db),
):
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
):
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
