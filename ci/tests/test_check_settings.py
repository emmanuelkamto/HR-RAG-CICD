"""Tests for ci/check_settings.py: hidden spaces and line breaks in GitHub settings."""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_settings

ROOT = Path(__file__).resolve().parents[2]


def good_settings():
    variables = {name: 'value' for name in check_settings.VARIABLES}
    variables['ENABLE_DEEPEVAL'] = 'true'
    variables['ENABLE_EVIDENTLY'] = 'false'
    secrets = {name: 'key' for name in check_settings.SECRETS}
    return variables, secrets


class CheckSettingsTests(unittest.TestCase):

    def test_clean_settings_pass(self):
        self.assertEqual(check_settings.check(*good_settings()), [])

    def test_a_pasted_line_break_is_named(self):
        variables, secrets = good_settings()
        variables['AWS_STAGING_ROLE_ARN'] = 'arn:aws:iam::123456789012:role/x\n'
        normalized, cleaned = check_settings.normalize_settings(check_settings.VARIABLES, variables)
        self.assertEqual(check_settings.check(normalized, secrets), [])
        self.assertEqual(cleaned, ['AWS_STAGING_ROLE_ARN'])

    def test_a_space_inside_is_named(self):
        variables, secrets = good_settings()
        variables['AWS_STAGING_ROLE_ARN'] = 'arn:aws:iam::123 456789012:role/x'
        self.assertEqual(check_settings.check(variables, secrets),
                         ['AWS_STAGING_ROLE_ARN contains a space or line break'])

    def test_a_missing_secret_is_named(self):
        variables, secrets = good_settings()
        secrets['LANGFUSE_SECRET_KEY'] = ''
        self.assertEqual(check_settings.check(variables, secrets), ['LANGFUSE_SECRET_KEY is missing or empty'])

    def test_a_secret_with_outer_space_is_named(self):
        variables, secrets = good_settings()
        secrets['LANGFUSE_SECRET_KEY'] = ' key '
        self.assertEqual(check_settings.check(variables, secrets),
                         ['LANGFUSE_SECRET_KEY contains a space or line break'])

    def test_switches_accept_only_true_or_false(self):
        variables, secrets = good_settings()
        variables['ENABLE_DEEPEVAL'] = 'yes'
        self.assertEqual(check_settings.check(variables, secrets), ['ENABLE_DEEPEVAL must be exactly true or false'])

    def test_the_names_match_the_settings_file(self):
        # scripts/github-settings.py writes the file students copy from. Both lists must agree.
        text = (ROOT / 'scripts' / 'github-settings.py').read_text(encoding='utf-8')
        written = re.findall(r"\('([A-Z_]+)', ", text)
        self.assertEqual(written, check_settings.VARIABLES + check_settings.SECRETS)


if __name__ == '__main__':
    unittest.main()
