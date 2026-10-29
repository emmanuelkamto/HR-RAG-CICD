"""Check the GitHub settings before the pipeline uses them. Runs first in the candidate job.

    python ci/check_settings.py

A value pasted into GitHub can carry a hidden space or line break. GitHub keeps it and does
not show it, and a later step then fails with an unclear error. This script names the
setting to fix instead. It never prints a value, so secrets stay hidden.

The workflow passes every variable as JSON in VARS_JSON, and the two secrets one by one.
"""
import json
import os
import sys

# The settings document 10 asks for, in the same order as build/github-settings.txt.
VARIABLES = [
    'AWS_REGION', 'AWS_STAGING_ROLE_ARN', 'HR_STAGING_FUNCTION', 'HR_EVALUATION_FUNCTION',
    'HR_STAGING_ORIGIN', 'HR_TEST_USERS_SECRET_ARN', 'HR_COGNITO_POOL_ID', 'HR_COGNITO_CLIENT_ID',
    'HR_STAGING_FRONTEND_BUCKET', 'HR_STAGING_DISTRIBUTION_ID', 'VITE_COGNITO_AUTHORITY',
    'VITE_COGNITO_DOMAIN', 'LANGFUSE_BASE_URL', 'ENABLE_DEEPEVAL', 'ENABLE_EVIDENTLY',
]
SECRETS = ['LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY']
SWITCHES = ['ENABLE_DEEPEVAL', 'ENABLE_EVIDENTLY']


def normalize_settings(names, values):
    """Strip hidden leading/trailing whitespace and report which names were cleaned."""
    normalized, cleaned = {}, []
    for name in names:
        raw = values.get(name)
        text = '' if raw is None else str(raw)
        stripped = text.strip()
        normalized[name] = stripped
        if text != stripped:
            cleaned.append(name)
    return normalized, cleaned


def problem_with(name, value):
    """What is wrong with one setting, as text, or None when it looks right."""
    if not value:
        return f'{name} is missing or empty'
    if any(character.isspace() for character in value):
        return f'{name} contains a space or line break'
    if name in SWITCHES and value not in ('true', 'false'):
        return f'{name} must be exactly true or false'
    return None


def check(variables, secrets):
    """Every problem found, as a list of text lines."""
    problems = []
    for name in VARIABLES:
        problems.append(problem_with(name, variables.get(name)))
    for name in SECRETS:
        problems.append(problem_with(name, secrets.get(name)))
    return [problem for problem in problems if problem]


def main():
    variables, cleaned_variables = normalize_settings(VARIABLES, json.loads(os.environ.get('VARS_JSON') or '{}'))
    secrets = {name: os.environ.get(name) for name in SECRETS}
    problems = check(variables, secrets)
    if problems:
        for problem in problems:
            print(problem)
        sys.exit('Fix these in GitHub: Settings > Environments > hr-staging. Paste only the value, '
                 'with nothing before or after it.')
    github_env = os.environ.get('GITHUB_ENV')
    if github_env:
        with open(github_env, 'a', encoding='utf-8') as handle:
            for name in VARIABLES:
                handle.write(f'{name}={variables[name]}\n')
    if cleaned_variables:
        print('Cleaned hidden leading/trailing whitespace for: ' + ', '.join(cleaned_variables))
    print(f'GitHub settings look right: {len(VARIABLES)} variables and {len(SECRETS)} secrets.')


if __name__ == '__main__':
    main()
