# User Guide: Bug Tracker Dashboard

## Get started
1. Open the app and choose **New here? Create an account**. Enter your email and a password of at least 8 characters.
2. The **first** account created becomes the **admin**. Everyone after that is a normal user.
3. Select **Register**, then sign in with the same email and password using **Sign in**.

## Report a bug
1. In **Report a bug** on the left, fill in **Title**, **Description** and **Priority** (Low, Medium or High).
2. Select **Add bug**. It appears at the top of the list with status **Open**.

## Track bugs
- The three cards at the top show how many bugs are **Open**, **In progress** and **Resolved**.
- Use the filter above the list to show one status.
- Change a bug's **Status** or **Priority** from its dropdowns.

## Admin only
- Choose an assignee from the dropdown (default **Unassigned**).
- Select **Delete** and confirm to remove a bug (this cannot be undone).

## Troubleshooting
| Problem | What to do |
| --- | --- |
| "Invalid email or password" | Check both. The message is the same for both on purpose, to protect accounts. |
| Page stays blank | You need internet on first load because React comes from a CDN. |
| Signed out suddenly | Sessions last 8 hours. Sign in again. |
