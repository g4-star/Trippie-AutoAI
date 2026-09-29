from __future__ import annotations

import hashlib
import re
from datetime import datetime
from urllib.parse import parse_qs, quote_plus, unquote, urlparse, urlunparse, urlencode, urljoin

import requests
from bs4 import BeautifulSoup

from .base import DiscoveryProvider


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    )
}
TIMEOUT = 15

EXPLICIT_LOCATION_TOKENS = (
    "germany",
    "united kingdom",
    "uk",
    "united states",
    "usa",
    "canada",
    "australia",
    "south africa",
    "uganda",
    "tanzania",
    "rwanda",
    "nigeria",
    "ghana",
    "india",
    "remote",
)

JOB_KEYWORDS = (
    "job",
    "jobs",
    "career",
    "careers",
    "vacancy",
    "vacancies",
    "employment",
    "opportunity",
    "opportunities",
    "position",
    "role",
    "internship",
    "recruitment",
)

BLOCK_KEYWORDS = (
    "verification required",
    "captcha",
    "verify you are human",
    "unusual traffic",
    "access denied",
    "cloudflare",
    "robot check",
)


class DuckDuckGoProvider(DiscoveryProvider):
    name = "duckduckgo"

    def _explicit_job_location(
        self,
        title: str,
        job_url: str,
    ) -> str:
        text = " ".join(
            [
                title or "",
                unquote(job_url or "").replace("-", " "),
            ]
        ).lower()

        for token in EXPLICIT_LOCATION_TOKENS:
            if re.search(
                rf"\b{re.escape(token)}\b",
                text,
            ):
                return token.title()

        return ""

    def _clean_url(self, url: str) -> str:
        parsed = urlparse(url)

        query = parse_qs(parsed.query)

        tracking_prefixes = (
            "utm_",
            "fbclid",
            "gclid",
            "msclkid",
        )

        linkedin_tracking = {
            "position",
            "pagenum",
            "refid",
            "trackingid",
        }

        query = {
            k: v
            for k, v in query.items()
            if not k.lower().startswith(tracking_prefixes)
            and not (
                "linkedin.com" in parsed.netloc.lower()
                and k.lower() in linkedin_tracking
            )
        }

        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc.lower(),
                parsed.path.rstrip("/"),
                parsed.params,
                urlencode(query, doseq=True),
                "",
            )
        )

    def _external_id(self, url: str) -> str:
        digest = hashlib.sha256(url.encode()).hexdigest()[:32]
        return f"web:{digest}"

    def _extract_url(self, anchor) -> str | None:
        href = anchor.get("href")

        if not href:
            return None

        if "uddg=" in href:
            target = parse_qs(urlparse(href).query).get("uddg")

            if target:
                return unquote(target[0])

        if href.startswith("//"):
            return "https:" + href

        if href.startswith("/"):
            return "https://html.duckduckgo.com" + href

        return href

    def _is_block_page(self, text: str) -> bool:
        lowered = text.lower()

        if any(
            keyword in lowered
            for keyword in BLOCK_KEYWORDS
        ):
            return True

        # Pages that are clearly services rather than vacancies.
        service_phrases = (
            "recruitment agency",
            "free job advertising",
            "career services",
            "cv customisation",
            "cv customization",
            "career advisory",
            "recruitment services",
            "staffing services",
        )

        if any(
            phrase in lowered
            for phrase in service_phrases
        ):
            return True

        return False

    def _looks_like_job_url(self, url: str) -> bool:
        lowered = url.lower()

        # LinkedIn individual public job pages.
        if "linkedin.com" in lowered:
            return "/jobs/view/" in lowered

        return any(
            keyword in lowered
            for keyword in JOB_KEYWORDS
        )

    def _is_valid_job_url(self, url: str) -> bool:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()

        # LinkedIn individual public job pages only.
        if "linkedin.com" in host:
            return path.startswith("/jobs/view/")

        # Reject obvious Corporate Staffing service/navigation pages.
        if "corporatestaffing.co.ke" in host:
            rejected_paths = (
                "/em/",
                "/job-advertising",
                "/cc",
                "/about",
                "/contact",
                "/services",
            )

            if any(
                path == rejected
                or path.startswith(rejected + "/")
                for rejected in rejected_paths
            ):
                return False

            # Their main jobs page is a listing, not an individual job.
            if path in ("/jobs", "/jobs/"):
                return False

        return True

    def _looks_like_listing_page(
        self,
        title: str,
        text: str,
        url: str,
    ) -> bool:
        lowered_title = title.lower()
        lowered_url = url.lower()

        # Obvious listing pages.
        listing_phrases = (
            "jobs in",
            "jobs kenya",
            "jobs by",
            "job listings",
            "job listing",
            "latest jobs",
            "all jobs",
            "vacancies in",
            "careers",
            "search jobs",
            "find jobs",
        )

        if any(
            phrase in lowered_title
            for phrase in listing_phrases
        ):
            return True

        # Common listing URL structures.
        listing_paths = (
            "/jobs",
            "/jobs/",
            "/jobs-by-",
            "/jobs-by-title/",
            "/tag/",
            "/search",
            "/career",
            "/careers",
            "/vacancies",
        )

        parsed = urlparse(lowered_url)
        path = parsed.path

        if any(
            path == p or path.startswith(p)
            for p in listing_paths
        ):
            # If the page contains many job-like links,
            # it is almost certainly an aggregator.
            if text.count("job") >= 8:
                return True

        return False

    def _extract_job_page(
        self,
        url: str,
        fallback_title: str = "",
    ) -> dict | None:
        """
        Fetch and extract a single individual job page.

        LinkedIn needs special handling because its public job pages contain
        large amounts of navigation/login boilerplate around the actual job.
        """
        try:
            r = self.session.get(url, timeout=self.timeout)
            if r.status_code != 200:
                return None

            html = r.text
            soup = BeautifulSoup(html, "html.parser")

            # Remove elements that are never part of the actual job content.
            for tag in soup([
                "script",
                "style",
                "noscript",
                "svg",
                "form",
                "header",
                "footer",
                "nav",
            ]):
                tag.decompose()

            raw_text = soup.get_text(" ", strip=True)
            raw_text = re.sub(r"\s+", " ", raw_text).strip()

            title = ""

            # Prefer OpenGraph/title metadata.
            og_title = soup.find("meta", attrs={"property": "og:title"})
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()

            if not title:
                title_tag = soup.find("title")
                if title_tag:
                    title = title_tag.get_text(" ", strip=True)

            # Clean LinkedIn title.
            if " | LinkedIn" in title:
                title = title.split(" | LinkedIn", 1)[0].strip()

            if title.startswith("LinkedIn"):
                title = title.replace("LinkedIn", "", 1).strip()

            # ---------------------------------------------------------
            # LINKEDIN-SPECIFIC METADATA
            # ---------------------------------------------------------
            is_linkedin = "linkedin.com" in url.lower()

            company = ""
            location = ""

            if is_linkedin:
                # Company fallback from LinkedIn URL:
                #
                # .../jobs/view/job-title-at-company-name-123456789/
                m = re.search(
                    r"/jobs/view/.+?-at-(.+?)-\d+(?:[/?#]|$)",
                    url,
                    re.IGNORECASE,
                )

                if m:
                    company_slug = m.group(1)
                    company = company_slug.replace("-", " ").strip()
                    company = re.sub(
                        r"\s+",
                        " ",
                        company,
                    ).title()

                # Known LinkedIn page pattern:
                # "Job Title at Company — Location | LinkedIn Jobs"
                title_meta = title

                m = re.search(
                    r"\bat\s+(.+?)\s*[—|-]\s*(.+?)\s*\|\s*LinkedIn",
                    title_meta,
                    re.IGNORECASE,
                )

                if m:
                    company = m.group(1).strip()
                    location = m.group(2).strip()

                # Another common pattern:
                # "Job Title in Nairobi, Kenya | LinkedIn"
                if not location:
                    m = re.search(
                        r"\bin\s+(.+?)\s*\|\s*LinkedIn",
                        title_meta,
                        re.IGNORECASE,
                    )
                    if m:
                        location = m.group(1).strip()

                # Extract location from visible job-page text.
                if not location:
                    location_patterns = [
                        r"\b(Nairobi(?:,\s*Nairobi County)?(?:,\s*Kenya)?)\b",
                        r"\b(Nakuru(?:,\s*Nakuru County)?(?:,\s*Kenya)?)\b",
                        r"\b(Mombasa(?:,\s*Mombasa County)?(?:,\s*Kenya)?)\b",
                        r"\b(Kisumu(?:,\s*Kisumu County)?(?:,\s*Kenya)?)\b",
                        r"\b(Kenya)\b",
                        r"\b(Remote)\b",
                        r"\b(Remote\s*-\s*Kenya)\b",
                    ]

                    for pattern in location_patterns:
                        m = re.search(
                            pattern,
                            raw_text,
                            re.IGNORECASE,
                        )
                        if m:
                            location = m.group(1).strip()
                            break

            # ---------------------------------------------------------
            # GENERIC FALLBACKS FOR NON-LINKEDIN JOB PAGES
            # ---------------------------------------------------------
            if not company:
                selectors = [
                    '[class*="company"]',
                    '[class*="employer"]',
                    '[data-testid*="company"]',
                    '[itemprop="hiringOrganization"]',
                ]

                for selector in selectors:
                    node = soup.select_one(selector)
                    if node:
                        text = node.get_text(" ", strip=True)
                        if text and len(text) < 200:
                            company = text
                            break

            if not location:
                selectors = [
                    '[class*="location"]',
                    '[data-testid*="location"]',
                    '[itemprop="jobLocation"]',
                ]

                for selector in selectors:
                    node = soup.select_one(selector)
                    if node:
                        text = node.get_text(" ", strip=True)
                        if text and len(text) < 200:
                            location = text
                            break

            # ---------------------------------------------------------
            # CLEAN JOB DESCRIPTION
            # ---------------------------------------------------------
            description = raw_text

            # Remove common LinkedIn boilerplate.
            boilerplate_patterns = [
                r"By clicking Continue to join or sign in, you agree to LinkedIn.*?(?=Job description|Job Summary|About the job|Overview|Responsibilities|Requirements)",
                r"Email or phone Password Show Forgot password\?.*?(?=Job description|Job Summary|About the job|Overview|Responsibilities|Requirements)",
                r"Sign in Sign in with Email or New to LinkedIn\?.*?(?=Job description|Job Summary|About the job|Overview|Responsibilities|Requirements)",
                r"Join now.*?(?=Job description|Job Summary|About the job|Overview|Responsibilities|Requirements)",
                r"Skip to main content.*?(?=Job description|Job Summary|About the job|Overview|Responsibilities|Requirements)",
            ]

            for pattern in boilerplate_patterns:
                description = re.sub(
                    pattern,
                    "",
                    description,
                    flags=re.IGNORECASE,
                )

            # Remove obvious navigation fragments.
            navigation_phrases = [
                "Jobs People Learning",
                "Clear text Clear text Clear text",
                "Use AI to assess how you fit",
                "Get AI-powered advice on this job and more exclusive features",
                "Sign in to evaluate your skills",
                "Sign in to tailor your resume",
            ]

            for phrase in navigation_phrases:
                description = description.replace(phrase, " ")

            description = re.sub(r"\s+", " ", description).strip()

            # If the page has an obvious job-description heading, keep
            # everything from that point onward.
            heading_patterns = [
                r"\bJob description:\s*(.*)",
                r"\bJob Description\s+(.*)",
                r"\bJob Summary:\s*(.*)",
                r"\bAbout the job\s+(.*)",
                r"\bOverview\s+(.*)",
            ]

            cleaned_description = description

            for pattern in heading_patterns:
                m = re.search(
                    pattern,
                    description,
                    re.IGNORECASE | re.DOTALL,
                )
                if m and len(m.group(1).strip()) > 300:
                    cleaned_description = m.group(1).strip()
                    break

            description = cleaned_description

            # Safety check: reject pages that still look like navigation,
            # authentication, or generic LinkedIn pages.
            if not title:
                title = fallback_title.strip()

            if not title:
                return None

            if len(description) < 250:
                return None

            lower = description.lower()

            if (
                "welcome to your professional community" in lower
                and len(description) < 1000
            ):
                return None

            # Requirements currently remain the same source text. The next
            # parser stage can split responsibilities/requirements/skills.
            requirements = description

            return {
                "external_id": hashlib.sha256(
                    url.encode("utf-8")
                ).hexdigest()[:24],
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "requirements": requirements,
                "job_url": url,
                "source": "duckduckgo",
                "discovered_at": datetime.utcnow().isoformat(),
            }

        except Exception:
            return None

    def _extract_candidate_links(
        self,
        base_url: str,
        soup: BeautifulSoup,
        max_links: int = 20,
    ) -> list[tuple[str, str]]:

        candidates = []
        seen = set()

        for anchor in soup.find_all("a", href=True):

            href = anchor.get("href", "").strip()

            if not href:
                continue

            absolute_url = urljoin(base_url, href)
            absolute_url = self._clean_url(absolute_url)

            if not self._is_valid_job_url(absolute_url):
                continue

            if absolute_url in seen:
                continue

            title = anchor.get_text(
                " ",
                strip=True,
            )

            if not title:
                title = anchor.get(
                    "aria-label",
                    "",
                ).strip()

            if not title:
                continue

            lower_title = title.lower()

            if any(
                phrase in lower_title
                for phrase in [
                    "sign in",
                    "log in",
                    "login",
                    "register",
                    "home",
                    "jobs home",
                    "search jobs",
                    "view all jobs",
                    "learn more",
                ]
            ):
                continue

            seen.add(absolute_url)

            candidates.append(
                (
                    absolute_url,
                    title,
                )
            )

            if len(candidates) >= max_links:
                break

        return candidates

    def _fetch_listing_jobs(
        self,
        url: str,
        fallback_title: str,
        limit: int,
    ) -> list[dict]:

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=20,
                allow_redirects=True,
            )

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(
                response.text,
                "html.parser",
            )

            raw_text = soup.get_text(
                " ",
                strip=True,
            )

            if self._is_block_page(raw_text):
                return []

            jobs = []
            seen = set()

            # LinkedIn public jobs listing pages expose complete
            # job-card metadata without requiring a second request
            # to the individual /jobs/view/ page.
            linkedin_cards = soup.select(
                "div.job-search-card"
            )

            for card in linkedin_cards:

                link = card.select_one(
                    'a[href*="/jobs/view/"]'
                )

                if not link:
                    continue

                job_url = self._clean_url(
                    link.get("href", "")
                )

                if not self._is_valid_job_url(job_url):
                    continue

                if job_url in seen:
                    continue

                seen.add(job_url)

                title_node = card.select_one(
                    ".base-search-card__title"
                )

                company_node = card.select_one(
                    ".base-search-card__subtitle"
                )

                location_node = card.select_one(
                    ".job-search-card__location"
                )

                title = (
                    title_node.get_text(
                        " ",
                        strip=True,
                    )
                    if title_node
                    else ""
                )

                company = (
                    company_node.get_text(
                        " ",
                        strip=True,
                    )
                    if company_node
                    else ""
                )

                location = (
                    location_node.get_text(
                        " ",
                        strip=True,
                    )
                    if location_node
                    else ""
                )

                explicit_location = self._explicit_job_location(
                    title,
                    job_url,
                )

                if explicit_location:
                    location = explicit_location

                if not title:
                    title = link.get_text(
                        " ",
                        strip=True,
                    )

                if not title:
                    continue

                # Keep the listing-card text as supporting metadata.
                # We deliberately do not label it as the full job
                # description because LinkedIn does not expose the
                # complete description on this listing page.
                card_text = card.get_text(
                    " ",
                    strip=True,
                )

                description, _ = self._fetch_linkedin_job_page(
                    job_url
                )

                jobs.append(
                    {
                        "external_id": self._external_id(
                            job_url
                        ),
                        "title": title,
                        "company": company,
                        "location": location,
                        "description": description,
                        "requirements": "",
                        "job_url": job_url,
                        "source": "linkedin",
                        "discovered_at": datetime.utcnow().isoformat(),
                        "metadata": {
                            "listing_text": card_text,
                            "listing_title": fallback_title,
                        },
                    }
                )

                if len(jobs) >= limit:
                    break

            # Generic fallback for non-LinkedIn listing pages.
            if not jobs:
                links = self._extract_candidate_links(
                    url,
                    soup,
                    max_links=min(limit * 3, 20),
                )

                for job_url, link_title in links:

                    if job_url in seen:
                        continue

                    seen.add(job_url)

                    job = self._extract_job_page(
                        job_url,
                        link_title,
                    )

                    if not job:
                        continue

                    jobs.append(job)

                    if len(jobs) >= limit:
                        break

            return jobs

        except requests.RequestException:
            return []


    def _fetch_linkedin_job_page(self, job_url: str) -> tuple[str, str]:
        try:
            response = requests.get(
                job_url,
                headers=HEADERS,
                timeout=TIMEOUT,
            )

            if response.status_code != 200:
                return "", ""

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(
                response.text,
                "html.parser",
            )

            node = (
                soup.select_one(".show-more-less-html__markup")
                or soup.select_one(".description__text")
                or soup.select_one(".decorated-job-posting__details")
            )

            description = (
                node.get_text(" ", strip=True)
                if node
                else ""
            )

            return description, ""

        except requests.RequestException:
            return "", ""

    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:

        search_url = (
            "https://html.duckduckgo.com/html/"
            f"?q={quote_plus(query)}"
        )

        response = requests.get(
            search_url,
            headers=HEADERS,
            timeout=20,
        )

        if response.status_code == 202:
            return []

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        results = []
        seen_urls = set()

        for anchor in soup.select("a.result__a"):

            target = self._extract_url(anchor)

            if not target:
                continue

            target = self._clean_url(target)

            parsed = urlparse(target)

            if parsed.scheme not in (
                "http",
                "https",
            ):
                continue

            if not parsed.netloc:
                continue

            if target in seen_urls:
                continue

            fallback_title = anchor.get_text(
                " ",
                strip=True,
            )

            if not fallback_title:
                continue

            seen_urls.add(target)

            # Fetch the search result page first.
            try:
                page_response = requests.get(
                    target,
                    headers=HEADERS,
                    timeout=15,
                    allow_redirects=True,
                )

                if page_response.status_code != 200:
                    continue

                page_soup = BeautifulSoup(
                    page_response.text,
                    "html.parser",
                )

                page_text = page_soup.get_text(
                    " ",
                    strip=True,
                )

                if self._is_block_page(page_text):
                    continue

            except requests.RequestException:
                continue

            # Aggregator/listing page:
            # extract individual jobs instead of storing
            # the whole listing page as one job.
            if self._looks_like_listing_page(
                fallback_title,
                page_text,
                target,
            ):
                remaining = limit - len(results)

                if remaining <= 0:
                    break

                listing_jobs = self._fetch_listing_jobs(
                    target,
                    fallback_title,
                    remaining,
                )

                for job in listing_jobs:

                    job_url = job["job_url"]

                    if job_url in seen_urls:
                        continue

                    seen_urls.add(job_url)
                    results.append(job)

                    if len(results) >= limit:
                        break

                if len(results) >= limit:
                    break

                continue

            # Otherwise treat the page as an individual job.
            job = self._extract_job_page(
                target,
                fallback_title,
            )

            if not job:
                continue

            if job["job_url"] in seen_urls:
                continue

            seen_urls.add(job["job_url"])
            results.append(job)

            if len(results) >= limit:
                break

        return results
