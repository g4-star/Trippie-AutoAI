import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.user import User
from app.services.job_analyzer import analyze_job


def _split_values(value: str | None) -> list[str]:
    if not value:
        return []

    return [
        item.strip().lower()
        for item in re.split(r"[,;\n|]+", value)
        if item.strip()
    ]


def _text(value: str | None) -> str:
    return (value or "").lower()


def _contains(text: str, term: str) -> bool:
    text = text.lower()
    term = term.strip().lower()

    if not term:
        return False

    if len(term) <= 3:
        return re.search(
            rf"\b{re.escape(term)}\b",
            text,
        ) is not None

    return term in text


def _has_remote_work_mode(job: Job) -> bool:
    """
    Detect actual remote/hybrid work wording.

    "Remote access" and "remote support" do not count
    as a remote job.
    """

    location = _text(job.location)

    location_terms = [
        "remote",
        "work from home",
        "work-from-home",
        "hybrid",
    ]

    if any(term in location for term in location_terms):
        return True

    description = _text(job.description)

    patterns = [
        r"\bfully remote\b",
        r"\bfully-remote\b",
        r"\bremote role\b",
        r"\bremote position\b",
        r"\bremote work\b",
        r"\bwork remotely\b",
        r"\bworking remotely\b",
        r"\bremote opportunity\b",
        r"\bopen to candidates anywhere\b",
        r"\bhybrid work\b",
        r"\bhybrid role\b",
    ]

    return any(
        re.search(pattern, description)
        for pattern in patterns
    )


SKILL_ALIASES = {
    "cybersecurity": [
        "cybersecurity",
        "cyber security",
        "information security",
        "security operations",
        "security controls",
        "security monitoring",
        "access control",
        "incident response",
        "vulnerability assessment",
        "vulnerability management",
    ],
    "linux": [
        "linux",
        "ubuntu",
        "debian",
        "red hat",
        "redhat",
        "rocky linux",
        "centos",
    ],
    "python": [
        "python",
        "python scripting",
    ],
    "networking": [
        "network administration",
        "network infrastructure",
        "networking",
        "tcp/ip",
        "tcp ip",
        "routing",
        "switching",
        "dns",
        "dhcp",
        "vlan",
    ],
    "firewall": [
        "firewall",
        "firewall administration",
        "firewall rules",
    ],
    "vpn": [
        "vpn",
        "vpn administration",
        "virtual private network",
    ],
    "bash": [
        "bash",
        "bash scripting",
    ],
    "sql": [
        "sql",
        "mysql",
        "postgresql",
        "postgres",
        "database",
    ],
    "git": [
        "git",
        "github",
        "gitlab",
        "version control",
    ],
    "javascript": [
        "javascript",
        "js",
    ],
    "react": [
        "react",
        "react.js",
        "reactjs",
    ],
    "flutter": [
        "flutter",
    ],
    "dart": [
        "dart",
    ],
    "supabase": [
        "supabase",
    ],
    "cloud": [
        "cloud",
        "aws",
        "azure",
        "google cloud",
        "gcp",
    ],
    "virtualization": [
        "virtualization",
        "vmware",
        "hyper-v",
        "proxmox",
        "virtual machines",
    ],
    "windows": [
        "windows server",
        "windows administration",
        "windows server administration",
    ],
}


CATEGORY_ALIASES = {
    "cybersecurity": [
        "cybersecurity",
        "cyber security",
        "information security",
        "security engineer",
        "security analyst",
        "soc analyst",
        "penetration tester",
        "penetration testing",
        "ethical hacking",
    ],
    "it": [
        "information technology",
        "it support",
        "it technician",
        "systems administrator",
        "system administrator",
        "network administrator",
        "technical support",
        "help desk",
        "infrastructure",
    ],
    "software development": [
        "software developer",
        "software engineer",
        "web developer",
        "frontend developer",
        "backend developer",
        "full stack developer",
        "full-stack developer",
        "mobile developer",
        "application developer",
    ],
    "data analysis": [
        "data analyst",
        "data analysis",
        "business analyst",
        "data scientist",
        "business intelligence",
        "bi analyst",
    ],
}


def _find_skill_matches(
    analyzed_skills: list[str],
    user_skills: list[str],
) -> list[str]:
    """
    Match the user's skills against skills extracted by
    the Job Analyzer.

    This is intentionally skill-first.
    """

    job_skills = {
        skill.strip().lower()
        for skill in analyzed_skills
        if skill.strip()
    }

    matches = []

    for user_skill in user_skills:
        aliases = SKILL_ALIASES.get(
            user_skill,
            [user_skill],
        )

        if user_skill in job_skills:
            matches.append(user_skill)
            continue

        # Analyzer may identify a canonical skill while
        # the user's profile uses a related alias.
        if any(
            alias in job_skills
            for alias in aliases
        ):
            matches.append(user_skill)

    return matches


def _find_category_matches(
    title: str,
    job_text: str,
    categories: list[str],
) -> list[str]:
    matches = []

    for category in categories:
        aliases = CATEGORY_ALIASES.get(
            category,
            [category],
        )

        if any(
            _contains(title, alias)
            for alias in aliases
        ):
            matches.append(category)
            continue

        if any(
            _contains(job_text, alias)
            for alias in aliases
        ):
            matches.append(category)

    return matches


def _responsibility_skill_alignment(
    analyzed_responsibilities: list[str],
    skill_hits: list[str],
) -> list[str]:
    """
    Identify responsibilities that contain evidence
    related to the user's matched skills.
    """

    aligned = []

    for responsibility in analyzed_responsibilities:
        text = responsibility.lower()

        matched = False

        for skill in skill_hits:
            aliases = SKILL_ALIASES.get(
                skill,
                [skill],
            )

            if any(
                _contains(text, alias)
                for alias in aliases
            ):
                matched = True
                break

        if matched:
            aligned.append(responsibility)

    return aligned


def calculate_match(
    job: Job,
    user: User,
) -> dict[str, Any]:
    """
    Skill-first transparent job matching.

    Education and experience are deliberately excluded
    from scoring.

    Score:
        Skills:           55
        Category:         20
        Responsibilities: 15
        Location:         10

    Education: 0
    Experience: 0
    """

    title = _text(job.title)

    description = _text(job.description)

    requirements = _text(job.requirements)

    job_text = " ".join(
        [
            title,
            description,
            requirements,
        ]
    )

    skills = _split_values(user.skills)

    categories = _split_values(
        user.preferred_categories
    )

    locations = _split_values(
        user.preferred_locations
    )

    # ---------------------------------------------------------
    # JOB ANALYSIS
    # ---------------------------------------------------------

    analysis = analyze_job(job)

    analyzed_skills = analysis["skills"]

    responsibilities = analysis["responsibilities"]

    # ---------------------------------------------------------
    # 1. SKILLS — 55 POINTS
    # ---------------------------------------------------------

    skill_hits = _find_skill_matches(
        analyzed_skills,
        skills,
    )

    if skills:
        denominator = max(
            1,
            min(len(skills), 8),
        )

        skill_score = round(
            min(
                1,
                len(skill_hits) / denominator,
            )
            * 55
        )
    else:
        skill_score = 0

    if skill_hits:
        reasons = [
            "Matching skills: "
            + ", ".join(skill_hits[:10])
        ]
    else:
        reasons = []

    concerns: list[str] = []

    if not skill_hits:
        concerns.append(
            "No profile skills matched the analyzed job skills."
        )

    # ---------------------------------------------------------
    # 2. CATEGORY — 20 POINTS
    # ---------------------------------------------------------

    category_hits = _find_category_matches(
        title,
        job_text,
        categories,
    )

    if category_hits:
        category_score = 20

        reasons.append(
            "Relevant job category: "
            + ", ".join(category_hits[:4])
        )
    else:
        category_score = 0

        concerns.append(
            "No strong job-category match found."
        )

    # ---------------------------------------------------------
    # 3. RESPONSIBILITIES — 15 POINTS
    # ---------------------------------------------------------

    aligned_responsibilities = (
        _responsibility_skill_alignment(
            responsibilities,
            skill_hits,
        )
    )

    if responsibilities:
        responsibility_ratio = (
            len(aligned_responsibilities)
            / len(responsibilities)
        )
    else:
        responsibility_ratio = 0

    responsibility_score = round(
        min(1, responsibility_ratio) * 15
    )

    if aligned_responsibilities:
        reasons.append(
            "Job responsibilities contain "
            "evidence related to your matched skills."
        )

    # ---------------------------------------------------------
    # 4. LOCATION — 10 POINTS
    # ---------------------------------------------------------

    job_location = _text(job.location)

    location_hits = [
        location
        for location in locations
        if _contains(job_location, location)
    ]

    if location_hits:
        location_score = 10

        reasons.append(
            "Preferred location match: "
            + ", ".join(location_hits[:3])
        )

    elif _has_remote_work_mode(job):
        location_score = 10

        reasons.append(
            "Job explicitly supports remote work."
        )

    elif not job_location:
        location_score = 5

        concerns.append(
            "Job location is unspecified."
        )

    else:
        location_score = 0

        concerns.append(
            f"Location may not match preferences: "
            f"{job.location}"
        )

    # ---------------------------------------------------------
    # FINAL SCORE
    # ---------------------------------------------------------

    score = min(
        100,
        skill_score
        + category_score
        + responsibility_score
        + location_score,
    )

    return {
        "score": score,
        "reasons": reasons,
        "concerns": concerns,
        "skill_matches": skill_hits,
        "missing_skills": sorted(
            set(analysis["skills"]) - set(skill_hits)
        ),
        "category_matches": category_hits,
        "responsibility_matches": aligned_responsibilities,
        "skill_score": skill_score,
        "category_score": category_score,
        "responsibility_score": responsibility_score,
        "location_score": location_score,
        "education_requirements": analysis[
            "education_requirements"
        ],
        "experience_requirements": analysis[
            "experience_requirements"
        ],
    }


def match_jobs_for_user(
    db: Session,
    user_id: int,
) -> dict[str, Any]:
    user = db.get(User, user_id)

    if not user:
        return {
            "user_id": user_id,
            "jobs_analyzed": 0,
            "matches": [],
            "error": "User not found.",
        }

    jobs = db.scalars(
        select(Job)
        .where(Job.is_active.is_(True))
        .order_by(Job.discovered_at.desc())
    ).all()

    matches = []

    for job in jobs:
        result = calculate_match(
            job=job,
            user=user,
        )

        job.match_score = result["score"]

        matches.append(
            {
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "score": result["score"],
                "reasons": result["reasons"],
                "concerns": result["concerns"],
                "skill_matches": result[
                    "skill_matches"
                ],
                "category_matches": result[
                    "category_matches"
                ],
                "responsibility_matches": result[
                    "responsibility_matches"
                ],
                "skill_score": result[
                    "skill_score"
                ],
                "category_score": result[
                    "category_score"
                ],
                "responsibility_score": result[
                    "responsibility_score"
                ],
                "location_score": result[
                    "location_score"
                ],
                "education_requirements": result[
                    "education_requirements"
                ],
                "experience_requirements": result[
                    "experience_requirements"
                ],
            }
        )

    db.commit()

    matches.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return {
        "user_id": user_id,
        "jobs_analyzed": len(jobs),
        "matches": matches,
    }
