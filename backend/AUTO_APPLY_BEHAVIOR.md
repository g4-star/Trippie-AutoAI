# TrippieAutoAI job matching and auto-apply behavior

TrippieAutoAI is a personal job-hunting agent focused on cybersecurity and IT/technology roles worldwide.

- Discovery searches cybersecurity, SOC, information security, IT support, systems/network/cloud, software development, QA, database, and data-analysis roles, including entry-level, internship, junior, apprenticeship, and volunteer opportunities.
- Non-IT categories such as supply chain, procurement, warehouse, logistics, and general marketing/HR roles are excluded from discovery results and application preparation.
- Matching is skill-first. Education and years-of-experience requirements are informational and must not independently lower the match score or reject a role.
- When the vacancy specifies an experience requirement, the cover letter may transparently acknowledge that the candidate may not yet meet the requested years, then emphasize verified matching skills. It must not invent qualifications, experience, projects, or eligibility.
- The daily application limit is enforced across worker cycles using application records created during the current UTC day. Existing records prevent duplicate applications.
- An application is marked `submitted` only after a supported provider integration confirms genuine successful submission. Sources without an implemented, authorized adapter are recorded as requiring manual action; the app must never report a draft or failed attempt as submitted.

## Provider integration status

Automated submission is provider-specific. The current submission service has no enabled provider adapters, so this change improves discovery, matching, and preparation but does not by itself submit applications to LinkedIn, BrighterMonday, or arbitrary career pages. Implement and test an authorized adapter per source before claiming end-to-end auto-submission for that source.
