from __future__ import annotations

from itertools import cycle

from sqlalchemy.orm import Session

from app.models.user import User


DEFAULT_SEARCHES = [
    "cybersecurity",
    "SOC analyst",
    "cybersecurity analyst",
    "information security",
    "security analyst",
    "cybersecurity intern",
    "IT support",
    "technical support",
    "IT intern",
    "software developer",
    "software developer intern",
    "junior software developer",
    "Python developer",
    "Flutter developer",
    "frontend developer",
    "React developer",
    "data analyst",
    "data analysis",
    "business analyst",
    "operations analyst",
    "supply chain",
    "demand planning",
    "inventory planning",
    "procurement",
]


def _split_values(value: str | None) -> list[str]:
    if not value:
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def build_search_queries(
    db: Session,
    user_id: int,
) -> list[str]:
    user = db.query(User).filter(User.id == user_id).first()

    roles = [
        "cybersecurity jobs",
        "SOC analyst jobs",
        "security analyst jobs",
        "information security jobs",
        "cybersecurity intern",
        "IT support jobs",
        "IT intern",
        "technical support jobs",
        "software developer jobs",
        "junior software developer jobs",
        "Python developer jobs",
        "Flutter developer jobs",
        "frontend developer jobs",
        "React developer jobs",
        "data analyst jobs",
        "data analysis jobs",
        "business analyst jobs",
        "operations analyst jobs",
        "supply chain jobs",
        "procurement jobs",
    ]

    locations = ["Kenya", "Uganda", "Remote"]

    if user:
        preferred = _split_values(user.preferred_locations)
        locations = [x for x in preferred if x] or locations

    queries = []

    for role in roles:
        queries.append(role)

    for location in locations:
        for role in roles:
            queries.append(f"{role} {location}")

    return list(dict.fromkeys(queries))[:80]
