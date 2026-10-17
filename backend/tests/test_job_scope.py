import unittest

from app.services.job_scope import is_target_job


class JobScopeTests(unittest.TestCase):
    def test_accepts_cybersecurity_roles(self):
        for title in ("SOC Analyst", "Cybersecurity Intern", "Information Security Engineer"):
            with self.subTest(title=title):
                self.assertTrue(is_target_job(title))

    def test_accepts_it_roles(self):
        for title in ("IT Support Officer", "Junior Software Developer", "Network Engineer", "Data Analyst"):
            with self.subTest(title=title):
                self.assertTrue(is_target_job(title))

    def test_rejects_non_it_roles(self):
        for title in ("Supply Chain Analyst", "Procurement Officer", "Warehouse Supervisor", "Marketing Manager"):
            with self.subTest(title=title):
                self.assertFalse(is_target_job(title))

    def test_generic_trainee_needs_multiple_technical_signals(self):
        self.assertTrue(is_target_job("Graduate Trainee", "Work with Linux, SIEM, Python scripting, and network security."))
        self.assertFalse(is_target_job("Graduate Trainee", "Coordinate office schedules and maintain filing records."))

    def test_missing_title_is_not_a_match(self):
        self.assertFalse(is_target_job(None, "Linux, Python, cybersecurity"))


if __name__ == "__main__":
    unittest.main()
