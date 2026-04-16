import unittest

from ingestion.resume_parser import parse_resume_to_profile
from utils.retry import call_with_retry


class IngestionAndRetryTests(unittest.TestCase):
    def test_parse_target_role_handles_empty_suffix(self):
        profile = parse_resume_to_profile('Jane Doe\nSummary line\nTarget role:')
        self.assertEqual(profile.target_role, '')

    def test_call_with_retry_rejects_non_positive_retries(self):
        with self.assertRaises(ValueError):
            call_with_retry(lambda: 'ok', retries=0)


if __name__ == '__main__':
    unittest.main()
