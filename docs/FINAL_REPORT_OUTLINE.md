# DreamAI Final Report Outline

This outline follows the structure requested in the coursework PDF and adapts it to the DreamAI project.

## Front matter

1. Title Sheet
2. Acknowledgements
3. Abstract
4. Table of Contents

## 1. Project Introduction

Include:

- project background and motivation
- team member list and roles
- project aim and objectives
- target audience
- problem statement
- main functionality
- non-functional requirements
- implementation environment
- budget summary
- timeline summary
- limitations
- stakeholder register

Use material from:

- `Readme.md`
- `docs/PROJECT_MANAGEMENT_PACK.md`

## 2. Project Organisation

Include:

- lifecycle model selection
- justification for iterative Agile-style approach
- team structure and role allocation
- organisation diagram
- reporting dependencies
- software development diagram

Use material from:

- `docs/PROJECT_MANAGEMENT_PACK.md`

## 3. Risk Analysis

Include:

- project risks
- product/technical risks
- business risks
- mitigation strategies
- explanation of high-priority risks

Use:

- risk register in `docs/PROJECT_MANAGEMENT_PACK.md`

## 4. Design and Implementation

Suggested subsections:

### 4.1 System architecture
- frontend, backend, database, AI module

### 4.2 Database design
- tables: `users`, `dreams`, `analysis_results`

### 4.3 Authentication and security
- password hashing
- session handling
- privacy notes

### 4.4 Dream analysis pipeline
- text submission
- emotion analysis
- keyword extraction
- recurring-pattern analysis

### 4.5 Frontend design
- login/register
- record dream
- dashboard
- history modal
- export

### 4.6 Testing
- unit tests
- validation checks
- demo scenarios

Reference source files:

- `backend/app.py`
- `backend/ai_model.py`
- `backend/models.py`
- `backend/password_utils.py`
- `database/init_db.py`
- `frontend/index.html`
- `frontend/js/app.js`
- `frontend/css/style.css`
- `backend/test_backend.py`

## 5. Results and Discussion

Cover:

- what the completed system can do
- example user workflow
- dashboard outputs
- recurring-pattern behaviour
- limitations in AI confidence and interpretation
- strengths and weaknesses of the final artefact

## 6. Review of Final Deliverable

Discuss:

- completeness against objectives
- usability
- reliability
- security improvements
- demo readiness

## 7. Marketing and Commercialisation

Include:

- target market
- market gap
- competitive positioning
- student wellbeing angle
- possible monetisation
- future growth opportunities

Use:

- `docs/PROJECT_MANAGEMENT_PACK.md`

## 8. Conclusions and Recommendations

Summarise:

- whether the aim and objectives were achieved
- key design and technical achievements
- what should be improved next

## 9. Future Work

Possible content:

- better dream datasets
- higher-quality personalised suggestions
- richer reports
- mobile app version
- sleep-tracker integration
- improved analytics and trend summaries

## 10. References

Use Harvard referencing as required by the module.

Likely references include:

- Flask documentation
- Hugging Face model documentation
- Chart.js documentation
- scikit-learn documentation
- academic sources related to sleep, dreams, and student wellbeing

## 11. Appendix

Suggested appendices:

- individual reflective reports
- group meeting minutes
- screenshots of UI
- design wireframes
- selected code samples
- test evidence

Template support file:

- `docs/GROUP_MEETING_TEMPLATE.md`

## Suggested evidence to capture before submission

1. Login screen
2. Dashboard with sample data
3. Record dream form
4. Successful analysis result
5. Dream history list
6. Dream detail modal
7. Exported JSON sample
8. Test run output
