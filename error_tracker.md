# InsightFlow AI - Resolved Errors & Bug Tracker

This document maintains a chronological record of all resolved bugs and issues in the InsightFlow AI project.

| Date | Bug / Issue | Root Cause | Resolution Details | Verification |
| :--- | :--- | :--- | :--- | :--- |
| **2026-07-10** | Stale dataset and data leakage when switching between user accounts. | 1. The frontend did not clear `active_dataset_id` from `localStorage` upon logging out.<br>2. The backend did not verify dataset ownership or filter queries/fallbacks by the authenticated user's ID. | 1. Cleared `active_dataset_id` in frontend `AuthContext` and `Layout` logout handlers.<br>2. Checked dataset existence in layout initialization and reset/cleared if not in the user's dataset list.<br>3. Implemented a `get_verified_dataset_id` helper in `deps.py` to assert dataset ownership in API routes.<br>4. Modified the schemas to allow empty string `dataset_id` in `DynamicDashboardResponse` when no datasets exist. | Added a new test `test_multi_user_dataset_isolation` to `tests/test_api.py` and ran the pytest test suite (10/10 tests passed). |
| **2026-07-12** | Backend startup launcher error: `Fatal error in launcher: Unable to create process using...` | The project directory was renamed from `3rd_sem_project` to `InsightFlow_AI`, rendering the hardcoded absolute shebang paths inside `.venv/Scripts/` executables (like `uvicorn.exe`, `pip.exe`) broken. | Recreated the virtual environment in place (`python -m venv --clear .venv`) and reinstalled dependencies from `requirements.txt` to compile valid script wrappers with updated local path references. | Ran the full backend integration and unit test suite (13/13 tests passed). |

