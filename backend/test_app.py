import os
import tempfile
import unittest

from app import create_app


class BugTrackerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.client = create_app(db_path=self.tmp.name, secret_key="test").test_client()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def register_login(self, email, password="password123"):
        self.client.post("/api/register", json={"email": email, "password": password})
        res = self.client.post("/api/login", json={"email": email, "password": password})
        return {"Authorization": "Bearer " + res.get_json()["token"]}

    def test_register_validation(self):
        bad_email = self.client.post("/api/register", json={"email": "nope", "password": "password123"})
        short_pw = self.client.post("/api/register", json={"email": "a@b.com", "password": "short"})
        self.assertEqual(bad_email.status_code, 400)
        self.assertEqual(short_pw.status_code, 400)

    def test_duplicate_email(self):
        self.register_login("a@b.com")
        res = self.client.post("/api/register", json={"email": "a@b.com", "password": "password123"})
        self.assertEqual(res.status_code, 409)

    def test_wrong_password_rejected(self):
        self.register_login("a@b.com")
        res = self.client.post("/api/login", json={"email": "a@b.com", "password": "wrongpass1"})
        self.assertEqual(res.status_code, 401)

    def test_bugs_require_token(self):
        self.assertEqual(self.client.get("/api/bugs").status_code, 401)
        res = self.client.get("/api/bugs", headers={"Authorization": "Bearer garbage"})
        self.assertEqual(res.status_code, 401)

    def test_create_and_list_bug(self):
        h = self.register_login("admin@x.com")
        res = self.client.post("/api/bugs", json={"title": "Login fails", "priority": "high"}, headers=h)
        self.assertEqual(res.status_code, 201)
        bugs = self.client.get("/api/bugs", headers=h).get_json()
        self.assertEqual(len(bugs), 1)
        self.assertEqual(bugs[0]["status"], "open")

    def test_bug_validation(self):
        h = self.register_login("admin@x.com")
        short = self.client.post("/api/bugs", json={"title": "ab"}, headers=h)
        bad_priority = self.client.post("/api/bugs", json={"title": "Valid title", "priority": "urgent"}, headers=h)
        self.assertEqual(short.status_code, 400)
        self.assertEqual(bad_priority.status_code, 400)

    def test_sql_injection_attempt_is_harmless(self):
        h = self.register_login("admin@x.com")
        self.client.post("/api/bugs", json={"title": "x'); DROP TABLE bugs;--"}, headers=h)
        res = self.client.get("/api/bugs", headers=h)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.get_json()), 1)

    def test_only_admin_can_assign_and_delete(self):
        admin = self.register_login("admin@x.com")  # first user is admin
        user = self.register_login("user@x.com")
        bug = self.client.post("/api/bugs", json={"title": "Crash on save"}, headers=user).get_json()
        users = self.client.get("/api/users", headers=admin).get_json()
        uid = next(u["id"] for u in users if u["email"] == "user@x.com")

        denied = self.client.patch(f"/api/bugs/{bug['id']}", json={"assignee_id": uid}, headers=user)
        self.assertEqual(denied.status_code, 403)
        ok = self.client.patch(f"/api/bugs/{bug['id']}", json={"assignee_id": uid}, headers=admin)
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(self.client.delete(f"/api/bugs/{bug['id']}", headers=user).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/bugs/{bug['id']}", headers=admin).status_code, 204)

    def test_other_users_cannot_edit_bug(self):
        self.register_login("admin@x.com")
        owner = self.register_login("owner@x.com")
        other = self.register_login("other@x.com")
        bug = self.client.post("/api/bugs", json={"title": "Layout broken"}, headers=owner).get_json()
        res = self.client.patch(f"/api/bugs/{bug['id']}", json={"status": "resolved"}, headers=other)
        self.assertEqual(res.status_code, 403)

    def test_stats(self):
        h = self.register_login("admin@x.com")
        self.client.post("/api/bugs", json={"title": "Bug one"}, headers=h)
        bug = self.client.post("/api/bugs", json={"title": "Bug two"}, headers=h).get_json()
        self.client.patch(f"/api/bugs/{bug['id']}", json={"status": "resolved"}, headers=h)
        stats = self.client.get("/api/stats", headers=h).get_json()
        self.assertEqual(stats, {"open": 1, "in_progress": 0, "resolved": 1})

    def test_bugs_include_reporter_and_assignee_emails(self):
        admin = self.register_login("admin@x.com")
        user = self.register_login("user@x.com")
        bug = self.client.post("/api/bugs", json={"title": "Crash on save"}, headers=user).get_json()
        self.assertEqual(bug["reporter_email"], "user@x.com")
        self.assertIsNone(bug["assignee_email"])
        uid = next(u["id"] for u in self.client.get("/api/users", headers=admin).get_json()
                   if u["email"] == "user@x.com")
        self.client.patch(f"/api/bugs/{bug['id']}", json={"assignee_id": uid}, headers=admin)
        listed = self.client.get("/api/bugs", headers=admin).get_json()[0]
        self.assertEqual(listed["assignee_email"], "user@x.com")

    def test_login_is_locked_after_repeated_failures(self):
        self.register_login("a@b.com")
        for _ in range(5):
            res = self.client.post("/api/login", json={"email": "a@b.com", "password": "wrongpass1"})
            self.assertEqual(res.status_code, 401)
        locked = self.client.post("/api/login", json={"email": "a@b.com", "password": "password123"})
        self.assertEqual(locked.status_code, 429)

    def test_successful_login_resets_failure_count(self):
        self.register_login("a@b.com")
        for _ in range(4):
            self.client.post("/api/login", json={"email": "a@b.com", "password": "wrongpass1"})
        ok = self.client.post("/api/login", json={"email": "a@b.com", "password": "password123"})
        self.assertEqual(ok.status_code, 200)
        again = self.client.post("/api/login", json={"email": "a@b.com", "password": "wrongpass1"})
        self.assertEqual(again.status_code, 401)

    def test_security_headers_present(self):
        res = self.client.get("/api/bugs")
        self.assertEqual(res.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(res.headers["X-Frame-Options"], "DENY")
        self.assertEqual(res.headers["Cache-Control"], "no-store")


if __name__ == "__main__":
    unittest.main()
