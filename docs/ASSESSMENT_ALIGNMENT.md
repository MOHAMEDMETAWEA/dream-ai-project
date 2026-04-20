# DreamAI Assessment Alignment

This file maps the project proposal and the final-report PDF requirements to the current repository.

## Proposal alignment

### Aim

Design and develop an AI-based system that helps users record and analyse dreams so they can better understand emotions and recurring patterns.

### Objectives covered

1. `Text and voice dream recording`
   - `frontend/index.html`
   - `frontend/js/app.js`

2. `AI-based emotion and recurring-symbol analysis`
   - `backend/ai_model.py`
   - `backend/app.py`

3. `Secure database-backed storage`
   - `database/init_db.py`
   - `backend/models.py`
   - `backend/password_utils.py`

### Applications covered

- student wellbeing reflection
- recurring stress-pattern awareness
- emotional self-monitoring over time
- simple report/export support through dashboard and JSON export

## PDF coursework alignment

### Task 1: Proposal support items

- `Project title, aim, objectives`
  - present in `Readme.md`
  - detailed in `docs/PROJECT_MANAGEMENT_PACK.md`

- `Market study`
  - `docs/PROJECT_MANAGEMENT_PACK.md`

- `Societal, risk, safety, and health implications`
  - `docs/PROJECT_MANAGEMENT_PACK.md`

- `Interface design, software tools, hardware`
  - `docs/PROJECT_MANAGEMENT_PACK.md`

- `Estimated cost breakdown and total budget`
  - `docs/PROJECT_MANAGEMENT_PACK.md`

- `Project planning chart and action plans`
  - `docs/PROJECT_MANAGEMENT_PACK.md`

### Task 2: Final report support items

- `Title / abstract / introduction support`
  - `Readme.md`
  - `docs/FINAL_REPORT_OUTLINE.md`

- `Stakeholder register`
  - `docs/PROJECT_MANAGEMENT_PACK.md`

- `Project organisation and lifecycle`
  - `docs/PROJECT_MANAGEMENT_PACK.md`

- `Risk register`
  - `docs/PROJECT_MANAGEMENT_PACK.md`

- `Design and implementation reference`
  - source code in `backend/`, `frontend/`, `database/`

- `Results / review of final deliverable`
  - application UI
  - backend test suite
  - `docs/FINAL_REPORT_OUTLINE.md`

- `Marketing and commercialisation`
  - `docs/PROJECT_MANAGEMENT_PACK.md`

- `Appendix support`
  - `docs/GROUP_MEETING_TEMPLATE.md`
  - source screenshots to be added during final report submission

### Task 3: Demonstration support

- `Working UI`
  - `frontend/`

- `Navigation and responsiveness`
  - `frontend/index.html`
  - `frontend/css/style.css`

- `Functional backend and database`
  - `backend/app.py`
  - `database/init_db.py`

- `Test evidence`
  - `backend/test_backend.py`

## Gaps now closed

- password hashing no longer depends on an extra `bcrypt` install just to seed data or run tests
- database path handling is now absolute and reliable
- dream entries now store real extracted keywords
- dashboard now supports data export through the UI
- frontend text has been cleaned up and launch behaviour is more robust
- coursework support docs are now included in the repository
