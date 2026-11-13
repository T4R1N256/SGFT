"""
Critical end-to-end tests with Playwright (WBS 3.4.8, 4.6). Owner: Yahir (pair: Jared, CI job).

They drive a real Chromium against Django's live server, so they only run when SGFT_E2E=1 (the CI job «E2E» sets
it): `SGFT_E2E=1 python manage.py test tests_e2e`. Without it, `python manage.py test` lists them as skipped.
"""
