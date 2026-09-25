import re
from typing import Any

from app.models.job import Job


SKILL_PATTERNS = {
    "cybersecurity": [
        "cybersecurity",
        "cyber security",
        "information security",
        "security monitoring",
        "security controls",
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


RESPONSIBILITY_PATTERNS = [
    "administer",
    "administration",
    "configure",
    "configuration",
    "deploy",
    "deployment",
    "develop",
    "development",
    "implement",
    "maintain",
    "maintenance",
    "monitor",
    "monitoring",
    "manage",
    "management",
    "support",
    "troubleshoot",
    "troubleshooting",
    "analyze",
    "analysis",
    "test",
    "testing",
    "assess",
    "assessment",
    "respond",
    "response",
]


EXPERIENCE_PATTERNS = [
    r"minimum of\s+(?:[a-z]+\s*)?\(?(\d+)\)?\s*(?:\+|or more)?\s*years?",
    r"at least\s+(?:[a-z]+\s*)?\(?(\d+)\)?\s*(?:\+|or more)?\s*years?",
    r"(?:[a-z]+\s*)?\(?(\d+)\)?\s*(?:\+|or more)?\s*years?\s+of\s+(?:relevant\s+)?experience",
    r"(?:[a-z]+\s*)?\(?(\d+)\)?\s*(?:\+|or more)?\s*years?\s+experience",
]


EDUCATION_PATTERNS = [
    r"\bbachelor(?:'s)?\s+degree\b[^.]*",
    r"\bmaster(?:'s)?\s+degree\b[^.]*",
    r"\bdiploma\b[^.]*",
    r"\bdegree\s+in\b[^.]*",
    r"\bundergraduate\s+degree\b[^.]*",
    r"\bpostgraduate\s+degree\b[^.]*",
]


def _text(value: str | None) -> str:
    return (value or "").strip()


def _contains(text: str, term: str) -> bool:
    text = text.lower()
    term = term.lower().strip()

    if not term:
        return False

    if len(term) <= 3:
        return re.search(
            rf"\b{re.escape(term)}\b",
            text,
        ) is not None

    return term in text


def _extract_skills(text: str) -> list[str]:
    found = []

    for skill, aliases in SKILL_PATTERNS.items():
        if any(
            _contains(text, alias)
            for alias in aliases
        ):
            found.append(skill)

    return found


def _extract_experience(text: str) -> str | None:
    numbers = []

    for pattern in EXPERIENCE_PATTERNS:
        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        for match in matches:
            if isinstance(match, tuple):
                match = match[0]

            try:
                numbers.append(int(match))
            except (TypeError, ValueError):
                continue

    if not numbers:
        return None

    years = max(numbers)

    return f"{years}+ years of experience requested"


def _extract_education(text: str) -> str | None:
    found = []

    for pattern in EDUCATION_PATTERNS:
        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        for match in matches:
            clean = " ".join(match.split())

            if clean and clean not in found:
                found.append(clean)

    if not found:
        return None

    return "; ".join(found[:5])


def _extract_responsibilities(text: str) -> list[str]:
    # Split on bullets/new lines/sentence boundaries.
    chunks = re.split(
        r"[•·\n]+|(?<=[.!?])\s+",
        text,
    )

    responsibilities = []

    for chunk in chunks:
        clean = " ".join(chunk.split())

        if len(clean) < 25:
            continue

        lower = clean.lower()

        # Do not classify education, experience,
        # qualifications, certifications, or skill-list
        # entries as responsibilities.
        if any(
            marker in lower
            for marker in [
                "years of experience",
                "years experience",
                "minimum of",
                "at least",
                "bachelor",
                "master",
                "degree in",
                "diploma",
                "qualifications and experience",
                "professional certifications",
                "preferred technical skills",
                "technical skills",
                "key competencies",
                "competencies",
                "ability to",
                "excellent communication",
                "strong understanding",
                "strong troubleshooting",
                "strong analytical",
            ]
        ):
            continue

        # A short technical label is a skill, not a responsibility.
        if (
            len(clean.split()) <= 8
            and (
                "administration" in lower
                or "management" in lower
                or "skills" in lower
                or lower.startswith("windows ")
                or lower.startswith("linux ")
                or lower.startswith("firewall ")
                or lower.startswith("cybersecurity ")
            )
        ):
            continue

        # Technical skill-list entries such as
        # "Linux Administration (Ubuntu, Debian, Red Hat)"
        # are skills, not responsibilities.
        if (
            len(clean.split()) <= 12
            and (
                "administration" in lower
                or "management" in lower
                or "virtualization" in lower
                or "cloud platforms" in lower
                or "network security" in lower
                or "access control" in lower
            )
            and not re.search(
                r"\b(will|responsible|candidate|role|perform|provide|support|conduct|install|create|manage|deploy|configure|maintain|monitor)\b",
                lower,
            )
        ):
            continue

        if any(
            keyword in lower
            for keyword in RESPONSIBILITY_PATTERNS
        ):
            responsibilities.append(clean)

    unique = []

    for item in responsibilities:
        if item not in unique:
            unique.append(item)

    return unique[:20]


def analyze_job(job: Job) -> dict[str, Any]:
    """
    Analyze a raw job posting.

    Education and experience are extracted separately for
    transparency. They are NOT part of the match score.
    """

    title = _text(job.title)
    description = _text(job.description)
    requirements = _text(job.requirements)

    full_text = " ".join(
        [
            title,
            description,
            requirements,
        ]
    )

    skills = _extract_skills(full_text)

    responsibilities = _extract_responsibilities(
        description
    )

    extracted_experience = (
        job.experience_requirements
        or _extract_experience(description)
    )

    extracted_education = (
        job.education_requirements
        or _extract_education(description)
    )

    return {
        "job_id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "skills": skills,
        "responsibilities": responsibilities,
        "education_requirements": extracted_education,
        "experience_requirements": extracted_experience,
        "employment_type": job.employment_type,
        "salary": job.salary,
        "date_posted": job.date_posted,
        "valid_through": job.valid_through,
        "job_url": job.job_url,
    }
