from __future__ import annotations

import re


CYBERSECURITY_TITLE_TERMS = (
    "cybersecurity", "cyber security", "information security", "infosec",
    "soc analyst", "security analyst", "security engineer", "security operations",
    "penetration tester", "penetration testing", "ethical hacker", "application security",
    "cloud security", "incident response", "threat hunter", "threat intelligence",
    "vulnerability analyst", "vulnerability management", "iam analyst", "grc analyst",
    "security consultant", "security architect",
)

IT_TITLE_TERMS = (
    "information technology", "it support", "it technician", "it officer", "it administrator",
    "help desk", "helpdesk", "service desk", "technical support", "desktop support",
    "systems administrator", "system administrator", "systems engineer", "network engineer",
    "network administrator", "network technician", "cloud engineer", "cloud administrator",
    "devops", "site reliability", "platform engineer", "software engineer", "software developer",
    "web developer", "frontend developer", "front-end developer", "backend developer",
    "back-end developer", "full stack developer", "full-stack developer", "mobile developer",
    "flutter developer", "python developer", "data analyst", "database administrator",
    "database engineer", "qa engineer", "quality assurance engineer", "test engineer",
    "technical analyst", "it analyst", "it manager", "technology analyst", "technology officer",
    "computer technician", "application developer", "systems analyst", "network security",
)

NON_TECH_TITLE_TERMS = (
    "supply chain", "procurement", "warehouse", "logistics", "demand planning",
    "accountant", "accounting", "human resources", "recruiter", "sales representative",
    "marketing manager", "customer care", "customer service representative",
)

TECHNICAL_SIGNALS = (
    "cybersecurity", "cyber security", "information security", "security operations",
    "incident response", "penetration testing", "vulnerability assessment", "siem",
    "linux", "windows server", "network administration", "tcp/ip", "firewall", "vpn",
    "python", "powershell", "bash scripting", "cloud infrastructure", "aws", "azure",
    "google cloud", "devops", "kubernetes", "docker", "sql", "database administration",
    "software development", "software engineering", "api development", "web development",
    "network engineer", "systems administration", "technical support", "help desk",
    "data analytics", "data analysis", "flutter", "react", "javascript", "typescript",
)


def is_target_job(
    title: str | None,
    description: str | None = None,
    requirements: str | None = None,
) -> bool:
    """Return True only for cybersecurity or IT/technology roles.

    A relevant role title is the strongest signal. Generic graduate/analyst roles
    are accepted only when the description contains multiple technical signals.
    Education and years of experience are intentionally not considered here.
    """
    normalized_title = re.sub(r"\s+", " ", (title or "").strip().lower())
    if not normalized_title:
        return False

    if any(term in normalized_title for term in NON_TECH_TITLE_TERMS):
        return False

    if any(term in normalized_title for term in CYBERSECURITY_TITLE_TERMS + IT_TITLE_TERMS):
        return True

    body = " ".join((description or "", requirements or "")).lower()
    signal_count = sum(1 for term in TECHNICAL_SIGNALS if term in body)
    generic_technical_titles = ("graduate trainee", "trainee", "intern", "analyst", "engineer", "technician", "specialist")
    return signal_count >= 2 and any(term in normalized_title for term in generic_technical_titles)
