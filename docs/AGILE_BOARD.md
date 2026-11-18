# Agile Board: Tasks and Acceptance Criteria

Create these as GitHub Issues (run `scripts/create_issues.sh`, or add them by hand), put them on a **GitHub Projects** board with columns *Todo, In progress, Done*, and close each one from a pull request (`Closes #3` in the PR description).

Working style to describe in interviews: small tasks, one branch per task, a short pull request, tests green in CI, then merge.

| # | Task | Labels | Acceptance criteria |
| --- | --- | --- | --- |
| 1 | Set up database schema, register and login | backend | Register and login tests pass; wrong password and unknown email give the same error. |
| 2 | Bug create, list, update and delete endpoints with validation | backend | Invalid status, priority and over-long text are rejected with clear messages. |
| 3 | Role-based access and stats endpoint | backend,security | Non-admin requests return 403; stats count bugs per status. |
| 4 | Write unit tests for the API | testing | `python -m unittest` passes locally and in CI. |
| 5 | Design all screens in Figma | design | Desktop and mobile frames for every screen; link added to README. |
| 6 | Build the React sign-in screen | frontend | Shows validation errors; keyboard accessible. |
| 7 | Build the React dashboard, form and bug list | frontend | Works for user and admin; empty and error states shown. |
| 8 | Match the UI to the Figma design | frontend,design | Desktop (1440) and mobile (375) match; side-by-side screenshots in docs/screenshots. |
| 9 | Accessibility pass | frontend | No contrast failures; usable with keyboard only. |
| 10 | Deploy a demo and add the link | devops | Live link and demo account details in README. |
| 11 | Write user and technical documentation | docs | A new teammate can run, use and understand the app from the docs. |
