# Test plan and acceptance evidence

## Automated checks

Run `python -m pytest -q` using the installed virtual environment. CSRF stays enabled in the tests: helpers obtain real tokens from rendered forms. Each test uses a separate temporary SQLite database. Normal user data is not touched.

| Requirement | Test function / coverage |
|---|---|
| FR-01 account access | `test_registration_hashing_and_authentication`, `test_duplicate_case_insensitive_username`, `test_invalid_registration` |
| FR-02 private CRUD | `test_create_edit_delete_and_confirmation`, `test_other_account_cannot_access_any_route_or_mutate`, `test_protected_pages_redirect_to_login` |
| FR-03 input validation | `test_invalid_application_does_not_save` (12 cases), `test_invalid_registration` (4 cases) |
| FR-04 search/filter | `test_search_filter_counts_literal_wildcards_and_pagination` |
| FR-05 dashboard/interviews | `test_upcoming_interviews_excludes_past_and_inactive`, search/dashboard test, `test_dashboard_status_totals` |
| FR-06 persistence | `test_restart_persistence`, `test_init_db_does_not_drop_data` |
| NFR-01 security | CSRF tests (6 paths), account isolation, escaped output, URL validation, redirect and header checks |
| NFR-03 server response target | `tests/benchmark.py`, 20 dashboard and 20 search requests with 1,000 seeded records |
| NFR-04 reliability | Invalid input preserves database; restart/init-db tests; demo repeated-run protection |
| NFR-02/NFR-05 usability/browsers | Manual checklist below; not verified automatically |

Actual automated outputs are saved in `test-results.txt` and `performance-results.json`. Timings are for the execution environment using Flask's test client, **not** the student's laptop, browser rendering, or a real network. Repeat on the target machine before claiming the full performance requirement has been met.

## Manual browser acceptance checklist (pending)

Run these on the actual laptop in both Chrome and Firefox. Record browser version, date, result, and any defect. A preview was attempted in the managed development environment, but its separate server could not access the installed Python runtime. No visual browser pass is claimed.

| ID | Action | Expected result | Recorded result |
|---|---|---|---|
| M-01 | Create a new account and sign out/in. | Valid credentials work; wrong credentials show an error. | Pending |
| M-02 | Add a company, position, date, status, URL, and notes. | Details display all saved values. | Pending |
| M-03 | Edit the position and status, save, then reload. | New values remain. | Pending |
| M-04 | Search by company; filter by Offer; clear. | Correct matching records; all records restored after clear. | Pending |
| M-05 | Create an Interview record with a future local time. | Appears under Next conversations. | Pending |
| M-06 | Change that status to Rejected or set a past date. | Removed from upcoming interviews; record remains in list. | Pending |
| M-07 | Open Delete, choose Keep, then delete a disposable record. | Cancel preserves it; confirmation removes it. | Pending |
| M-08 | Stop/start server; sign in. | Records remain unchanged. | Pending |
| M-09 | Use a second account. | First account's data is absent; direct record link returns 404. | Pending |
| M-10 | Resize to desktop and approximately 390px wide; use keyboard Tab. | Labels/buttons readable, focused controls visible, table scrollable, forms usable. | Pending |
| M-11 | Volunteer follows README to add, edit, filter, and delete without developer help. | Completes all four tasks. Record actual feedback. | Pending |
| M-12 | Repeat 1,000-record benchmark locally. | At least 19/20 requests for each endpoint finish within two seconds. | Pending |

## First-run regression

`test_first_start_creates_secret_and_restart_reuses_it` verifies startup without a configured secret and reuse after restart. It reproduced the reported `Path.open(..., opener=...)` TypeError before the correction and passes with built-in `open(...)`.

## Defect log

Do not invent failures, review participants, or results. Add real findings below.

| ID | Reproduction | Expected / actual | Severity | Fix / retest |
|---|---|---|---|---|
| BUG-01 | First launch without an existing session secret | Login starts / TypeError before server startup | Blocks startup | Use built-in open; regression test added and passing |
| ENV-01 | Start managed preview with the local Python virtual environment | Preview starts / runtime path unavailable in separate preview environment | Environment limitation; blocks browser QA here | Browser review remains pending on the student's laptop |

## Release acceptance

Core automated checks must pass; no known core-workflow or data-isolation defect may remain. Complete the pending manual checks before describing the application as fully accepted. Keep actual test evidence with the final report.
