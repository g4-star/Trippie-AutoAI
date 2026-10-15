from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User


DEFAULT_SEARCHES = [
    "cybersecurity", "SOC analyst", "cybersecurity analyst",
    "information security", "security analyst", "IT support",
    "technical support", "software developer", "Python developer",
    "Flutter developer", "frontend developer", "React developer",
    "data analyst", "business analyst", "operations analyst",
    "supply chain", "demand planning", "procurement",
]

ROLE_SEARCHES = [
    "cybersecurity jobs",
    "SOC analyst jobs",
    "security analyst jobs",
    "information security jobs",
    "cybersecurity internship",
    "IT support jobs",
    "IT internship",
    "technical support jobs",
    "software developer jobs",
    "junior software developer jobs",
    "Python developer jobs",
    "Flutter developer jobs",
    "frontend developer jobs",
    "React developer jobs",
    "data analyst jobs",
    "business analyst jobs",
    "operations analyst jobs",
    "supply chain jobs",
    "procurement jobs",
    "IT volunteer opportunities",
    "cybersecurity volunteer opportunities",
    "technology apprenticeship",
    "IT trainee jobs",
    "graduate technology jobs",
    "entry level technology jobs",
]

GLOBAL_LOCATIONS = [
    "Remote",
    "Worldwide",
    "Africa",
    "East Africa",
    "Kenya",
    "Uganda",
    "Tanzania",
    "Rwanda",
    "Ghana",
    "Nigeria",
    "South Africa",
    "United Kingdom",
    "Europe",
    "United States",
    "Canada",
    "Australia",
]


def _split_values(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def build_search_queries(db: Session, user_id: int) -> list[str]:
    user = db.query(User).filter(User.id == user_id).first()

    preferred = _split_values(user.preferred_locations) if user else []
    locations = list(dict.fromkeys(preferred + GLOBAL_LOCATIONS))

    queries: list[str] = []

    # Broad role searches help discover opportunities without a location filter.
    queries.extend(ROLE_SEARCHES)

    # Interleave location searches so no single country dominates the rotation.
    for location in locations:
        for role in ROLE_SEARCHES:
            queries.append(f"{role} {location}")

    # Explicitly search common experience-friendly opportunity types.
    for role in DEFAULT_SEARCHES:
        queries.extend([
            f"{role} internship",
            f"{role} entry level",
            f"{role} junior",
            f"{role} volunteer",
            f"{role} apprenticeship",
        ])

    return list(dict.fromkeys(queries))
