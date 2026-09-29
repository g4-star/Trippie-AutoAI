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
        "soc",
        "security operations",
        "penetration testing",
        "ethical hacking",
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
        "relational database",
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
    "typescript": [
        "typescript",
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
    "html": [
        "html",
        "html5",
    ],
    "css": [
        "css",
        "css3",
    ],
    "supabase": [
        "supabase",
    ],
    "cloud": [
        "cloud",
        "aws",
        "amazon web services",
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
        "active directory",
    ],
    "technical support": [
        "technical support",
        "tech support",
        "help desk",
        "helpdesk",
        "desktop support",
        "it support",
    ],
    "troubleshooting": [
        "troubleshooting",
        "technical troubleshooting",
        "system troubleshooting",
    ],
    "ticketing": [
        "ticketing system",
        "ticket management",
        "service desk",
        "servicedesk",
    ],
    "hardware": [
        "hardware support",
        "computer hardware",
        "hardware troubleshooting",
    ],
    "excel": [
        "excel",
        "microsoft excel",
        "ms excel",
        "spreadsheet",
        "spreadsheets",
    ],
    "data analysis": [
        "data analysis",
        "data analytics",
        "data analyst",
        "analytical skills",
        "analytics",
    ],
    "power bi": [
        "power bi",
        "powerbi",
    ],
    "tableau": [
        "tableau",
    ],
    "statistics": [
        "statistics",
        "statistical analysis",
    ],
    "forecasting": [
        "forecasting",
        "forecast",
        "demand forecasting",
    ],
    "demand planning": [
        "demand planning",
        "demand planner",
    ],
    "inventory management": [
        "inventory management",
        "inventory planning",
        "inventory control",
        "stock management",
        "stock control",
    ],
    "supply chain": [
        "supply chain",
        "supply chain management",
        "supply chain operations",
    ],
    "procurement": [
        "procurement",
        "procurement coordination",
        "purchasing",
        "purchasing operations",
    ],
    "purchase orders": [
        "purchase order",
        "purchase orders",
        "po coordination",
        "purchase order coordination",
    ],
    "supplier management": [
        "supplier management",
        "supplier follow-up",
        "vendor management",
        "vendor relations",
    ],
    "logistics": [
        "logistics",
        "warehouse",
        "warehouse operations",
        "warehousing",
    ],
    "project management": [
        "project management",
        "project coordination",
        "project planning",
    ],
    "technical support": [
        "technical support",
        "it support",
        "help desk",
        "service desk",
    ],
    "troubleshooting": [
        "troubleshooting",
        "troubleshoot",
        "technical troubleshooting",
    ],
    "documentation": [
        "documentation",
        "technical documentation",
        "report writing",
    ],
    "communication": [
        "communication skills",
        "written communication",
        "verbal communication",
        "stakeholder communication",
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
    "implementation",
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
    "coordinate",
    "coordination",
    "forecast",
    "forecasting",
    "plan",
    "planning",
    "track",
    "tracking",
    "review",
    "report",
    "reporting",
    "optimize",
    "optimization",
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
    chunks = re.split(
        r"[•·\n]+|(?<=[.!?])\s+",
        text,
    )

    responsibilities = []

    action_starters = (
        "administer", "configure", "deploy", "develop",
        "implement", "maintain", "monitor", "manage",
        "support", "troubleshoot", "analyze", "test",
        "assess", "respond", "coordinate", "forecast",
        "design", "build", "create", "automate",
        "investigate", "resolve", "review", "document",
        "lead", "deliver", "operate", "install",
    )

    for chunk in chunks:
        clean = " ".join(chunk.split())

        if len(clean) < 25 or len(clean.split()) > 45:
            continue

        lower = clean.lower()

        excluded_markers = (
            "create a job alert",
            "interested in building your career",
            "job application",
            "apply for this job",
            "apply now",
            "view all jobs",
            "view more jobs",
            "sign in",
            "log in",
            "privacy policy",
            "terms of use",
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
        )

        if any(marker in lower for marker in excluded_markers):
            continue

        first_word = re.sub(
            r"^[^a-zA-Z]+",
            "",
            lower,
        ).split(" ", 1)[0]

        if first_word in action_starters:
            responsibilities.append(clean)

    unique = []

    for item in responsibilities:
        if item not in unique:
            unique.append(item)

    return unique[:25]



def analyze_job(job: Job) -> dict[str, Any]:
    """
    Analyze a raw job posting.

    Education and experience are extracted separately
    for transparency and are never used as negative
    match criteria.
    """

    title = _text(job.title)
    description = _text(job.description)
    requirements = _text(job.requirements)

    full_text = " ".join(
        [
            title,
            description,
            requirements,
            _text(job.experience_requirements),
            _text(job.education_requirements),
        ]
    )

    skills = _extract_skills(full_text)

    responsibilities = _extract_responsibilities(
        description
    )

    extracted_experience = (
        job.experience_requirements
        or _extract_experience(full_text)
    )

    extracted_education = (
        job.education_requirements
        or _extract_education(full_text)
    )

    return {
        "job_id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "skills": skills,
        "required_skills": skills,
        "preferred_skills": [],
        "responsibilities": responsibilities,
        "education_requirements": extracted_education,
        "experience_requirements": extracted_experience,
        "employment_type": job.employment_type,
        "salary": job.salary,
        "date_posted": job.date_posted,
        "valid_through": job.valid_through,
        "job_url": job.job_url,
    }
