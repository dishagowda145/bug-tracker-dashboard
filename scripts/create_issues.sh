#!/usr/bin/env bash
# Creates the project issues on GitHub. Needs the GitHub CLI: https://cli.github.com (run `gh auth login` once).
# Run from inside your cloned repo:  bash scripts/create_issues.sh
set -e

gh label create "backend" --force >/dev/null
gh label create "design" --force >/dev/null
gh label create "devops" --force >/dev/null
gh label create "docs" --force >/dev/null
gh label create "frontend" --force >/dev/null
gh label create "security" --force >/dev/null
gh label create "testing" --force >/dev/null

gh issue create --title "Set up database schema, register and login" --label "backend" --body $'Users can register and sign in; passwords are hashed.\n\n**Acceptance criteria**\n- Register and login tests pass; wrong password and unknown email give the same error.'
gh issue create --title "Bug create, list, update and delete endpoints with validation" --label "backend" --body $'CRUD API for bugs with input validation.\n\n**Acceptance criteria**\n- Invalid status, priority and over-long text are rejected with clear messages.'
gh issue create --title "Role-based access and stats endpoint" --label "backend,security" --body $'Admins assign and delete; users edit only their own or assigned bugs.\n\n**Acceptance criteria**\n- Non-admin requests return 403; stats count bugs per status.'
gh issue create --title "Write unit tests for the API" --label "testing" --body $'Cover happy paths, validation, access control and SQL injection.\n\n**Acceptance criteria**\n- `python -m unittest` passes locally and in CI.'
gh issue create --title "Design all screens in Figma" --label "design" --body $'Create the Figma file from docs/FIGMA_DESIGN_SPEC.md.\n\n**Acceptance criteria**\n- Desktop and mobile frames for every screen; link added to README.'
gh issue create --title "Build the React sign-in screen" --label "frontend" --body $'Sign in and register card.\n\n**Acceptance criteria**\n- Shows validation errors; keyboard accessible.'
gh issue create --title "Build the React dashboard, form and bug list" --label "frontend" --body $'Summary cards, report form, filtered list, admin controls.\n\n**Acceptance criteria**\n- Works for user and admin; empty and error states shown.'
gh issue create --title "Match the UI to the Figma design" --label "frontend,design" --body $'Compare each frame to the page in Dev Mode and fix differences.\n\n**Acceptance criteria**\n- Desktop (1440) and mobile (375) match; side-by-side screenshots in docs/screenshots.'
gh issue create --title "Accessibility pass" --label "frontend" --body $'Contrast, labels, focus rings, tap targets.\n\n**Acceptance criteria**\n- No contrast failures; usable with keyboard only.'
gh issue create --title "Deploy a demo and add the link" --label "devops" --body $'Deploy with render.yaml.\n\n**Acceptance criteria**\n- Live link and demo account details in README.'
gh issue create --title "Write user and technical documentation" --label "docs" --body $'Keep docs/ up to date.\n\n**Acceptance criteria**\n- A new teammate can run, use and understand the app from the docs.'
