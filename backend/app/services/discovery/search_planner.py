from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User


# TrippieAutoAI deliberately searches cybersecurity and IT/technology roles only.
ROLE_SEARCHES = [
    "cybersecurity jobs", "SOC analyst jobs", "junior SOC analyst jobs",
    "security analyst jobs", "information security jobs", "penetration testing jobs",
    "vulnerability management jobs", "incident response jobs", "GRC analyst jobs",
    "cybersecurity internship", "cybersecurity graduate trainee", "IT support jobs",
    "IT help desk jobs", "service desk analyst jobs", "IT internship",
    "technical support jobs", "systems administrator jobs", "network engineer jobs",
    "cloud engineer jobs", "junior DevOps engineer jobs", "software developer jobs",
    "junior software developer jobs", "Python developer jobs", "Flutter developer jobs",
    "frontend developer jobs", "React developer jobs", "backend developer jobs",
    "data analyst jobs", "database administrator jobs", "QA engineer jobs",
    "IT volunteer opportunities", "cybersecurity volunteer opportunities",
    "technology apprenticeship", "IT trainee jobs", "graduate technology jobs",
    "entry level technology jobs",
]

GLOBAL_LOCATIONS = [
    "Remote", "Worldwide", "Africa", "East Africa", "Kenya", "Uganda", "Tanzania",
    "Rwanda", "Ghana", "Nigeria", "South Africa", "United Kingdom", "Europe",
    "United States", "Canada", "Australia", "Germany", "Netherlands", "India",
    "United Arab Emirates",
]


def _split_values(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def build_search_queries(db: Session, user_id: int) -> list[str]:
    user = db.query(User).filter(User.id == user_id).first()
    preferred = _split_values(user.preferred_locations) if user else []
    locations = list(dict.fromkeys(preferred + GLOBAL_LOCATIONS))
    queries: list[str] = list(ROLE_SEARCHES)

    # Search each role globally and in preferred/world regions. Rotation in the
    # discovery engine prevents a single location from monopolizing each cycle.
    for location in locations:
        for role in ROLE_SEARCHES:
            queries.append(f"{role} {location}")

    for role in ROLE_SEARCHES:
        base = role.removesuffix(" jobs").removesuffix(" job")
        queries.extend([
            f"{base} internship", f"{base} entry level", f"{base} junior",
            f"{base} volunteer", f"{base} apprenticeship",
        ])

    return list(dict.fromkeys(queries))
