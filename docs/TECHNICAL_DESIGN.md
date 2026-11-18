# Technical Design: Bug Tracker Dashboard

## Goal
Let a small team report bugs, assign them, and watch progress on one dashboard, with sign-in and role-based access.

## Users and requirements
| User | Needs |
| --- | --- |
| Reporter (normal user) | Sign in, report a bug, see the list, update status or priority of their own or assigned bugs |
| Admin (first account) | Everything above, plus assign bugs and delete bugs |

## Architecture
```
Browser (React, no build step)  --JSON over HTTP-->  Flask REST API  --parameterised SQL-->  SQLite
```
- **Front end:** React components in `frontend/app.jsx`, plain CSS in `styles.css`. Loaded from a CDN so there is no build step.
- **API:** Flask app factory `create_app()` in `backend/app.py`. Easy to test with a temporary database.
- **Database:** SQLite file, two tables.

## Data model
| Table | Columns |
| --- | --- |
| users | id, email (unique), password_hash, role (`user` or `admin`) |
| bugs | id, title, description, status (`open`, `in_progress`, `resolved`), priority (`low`, `medium`, `high`), reporter_id, assignee_id, created_at |

## Security and privacy decisions
| Decision | Why |
| --- | --- |
| Passwords hashed with Werkzeug | A database leak does not reveal passwords |
| Signed tokens that expire after 8 hours | No server session storage and limited damage if stolen |
| Parameterised SQL everywhere | Prevents SQL injection (covered by a test) |
| Validation of every input | Rejects bad email, short password, over-long text, unknown status or priority |
| Same error for wrong password and unknown email | Does not reveal which emails have accounts (user privacy) |
| Role checks on the server | Hiding a button in the UI is not security |
| React escapes rendered text | Prevents stored XSS from bug titles |
| `SECRET_KEY` from the environment | No secrets in the repository |

## Trade-offs
- SQLite is simple and perfect for a demo, but a team product would move to PostgreSQL.
- The token is kept in browser memory or storage. A hardened version would use an HTTP-only cookie.
- There is no password reset or rate limiting yet (see "Ideas to extend it").

## Testing
`python -m unittest -v` runs API tests for registration, login, validation, role rules, SQL-injection attempts and stats. CI runs them on every push.

## Future work
Comments and activity history, search and pagination, React component tests, HTTP-only cookies, login rate limiting.
