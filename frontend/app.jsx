const { useState, useEffect, useCallback } = React;

// ---- API helper: attaches the token and turns errors into messages ----
async function api(path, { method = "GET", body, token } = {}) {
  const res = await fetch("/api" + path, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: "Bearer " + token } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.error || "Something went wrong");
    err.status = res.status;
    throw err;
  }
  return data;
}

const STATUS_LABEL = { open: "Open", in_progress: "In progress", resolved: "Resolved" };

// ---- Login / register screen ----
function AuthScreen({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") {
        await api("/register", { method: "POST", body: { email, password } });
      }
      const data = await api("/login", { method: "POST", body: { email, password } });
      onLogin(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-card">
      <h1>Bug Tracker</h1>
      <p className="muted">{mode === "login" ? "Sign in to continue" : "Create your account"}</p>
      <form onSubmit={submit}>
        <label>Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>Password
          <input type="password" value={password} minLength={8}
                 onChange={(e) => setPassword(e.target.value)} required />
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button type="submit" disabled={busy}>{mode === "login" ? "Sign in" : "Register"}</button>
      </form>
      <button className="link" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>
        {mode === "login" ? "New here? Create an account" : "Have an account? Sign in"}
      </button>
    </main>
  );
}

// ---- Summary cards ----
function StatCards({ stats }) {
  return (
    <section className="cards" aria-label="Bug summary">
      {Object.keys(STATUS_LABEL).map((s) => (
        <div key={s} className={"card " + s}>
          <span className="count">{stats[s] ?? 0}</span>
          <span>{STATUS_LABEL[s]}</span>
        </div>
      ))}
    </section>
  );
}

// ---- New bug form ----
function BugForm({ token, onCreated }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      await api("/bugs", { method: "POST", token, body: { title, description, priority } });
      setTitle(""); setDescription(""); setPriority("medium");
      onCreated();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="panel" onSubmit={submit}>
      <h2>Report a bug</h2>
      <label>Title
        <input value={title} onChange={(e) => setTitle(e.target.value)} maxLength={120} required />
      </label>
      <label>Description
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} maxLength={2000} rows={3} />
      </label>
      <label>Priority
        <select value={priority} onChange={(e) => setPriority(e.target.value)}>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </label>
      {error && <p className="error" role="alert">{error}</p>}
      <button type="submit">Add bug</button>
    </form>
  );
}

// ---- One bug row ----
function BugRow({ bug, users, me, token, onChanged }) {
  const isAdmin = me.role === "admin";
  const canEdit = isAdmin || bug.reporter_id === me.id || bug.assignee_id === me.id;

  async function patch(changes) {
    try {
      await api("/bugs/" + bug.id, { method: "PATCH", token, body: changes });
      onChanged();
    } catch (err) {
      alert(err.message);
    }
  }
  async function remove() {
    if (!confirm("Delete this bug?")) return;
    try {
      await api("/bugs/" + bug.id, { method: "DELETE", token });
      onChanged();
    } catch (err) {
      alert(err.message);
    }
  }

  return (
    <li className="bug">
      <div className="bug-head">
        <strong>#{bug.id} {bug.title}</strong>
        <span className={"badge " + bug.priority}>{bug.priority}</span>
      </div>
      {bug.description && <p className="muted">{bug.description}</p>}
      <p className="muted small">
        Reported by {bug.reporter_email}
        {bug.assignee_email && <> · Assigned to {bug.assignee_email}</>}
      </p>
      <div className="bug-actions">
        <label>Status
          <select value={bug.status} disabled={!canEdit} onChange={(e) => patch({ status: e.target.value })}>
            {Object.entries(STATUS_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        {isAdmin && (
          <label>Assignee
            <select value={bug.assignee_id ?? ""}
                    onChange={(e) => patch({ assignee_id: e.target.value ? Number(e.target.value) : null })}>
              <option value="">Unassigned</option>
              {users.map((u) => <option key={u.id} value={u.id}>{u.email}</option>)}
            </select>
          </label>
        )}
        {isAdmin && <button className="danger" onClick={remove}>Delete</button>}
      </div>
    </li>
  );
}

// ---- Dashboard ----
function Dashboard({ session, onLogout }) {
  const { token } = session;
  const [me, setMe] = useState(null);
  const [users, setUsers] = useState([]);
  const [bugs, setBugs] = useState([]);
  const [stats, setStats] = useState({});
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const query = filter ? "?status=" + filter : "";
      const [b, s, u] = await Promise.all([
        api("/bugs" + query, { token }),
        api("/stats", { token }),
        api("/users", { token }),
      ]);
      setBugs(b); setStats(s); setUsers(u);
      setMe(u.find((x) => x.email === session.email));
      setError("");
    } catch (err) {
      if (err.status === 401) onLogout();
      else setError(err.message);
    }
  }, [filter, token]);

  useEffect(() => { load(); }, [load]);

  if (!me) return <p className="muted center">Loading…</p>;

  return (
    <div className="layout">
      <header>
        <h1>Bug Tracker</h1>
        <div>
          <span className="muted">{me.email} ({me.role})</span>
          <button className="link" onClick={onLogout}>Sign out</button>
        </div>
      </header>
      {error && <p className="error" role="alert">{error}</p>}
      <StatCards stats={stats} />
      <div className="columns">
        <BugForm token={token} onCreated={load} />
        <section className="panel">
          <div className="list-head">
            <h2>Bugs</h2>
            <select value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filter by status">
              <option value="">All</option>
              {Object.entries(STATUS_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>
          {bugs.length === 0 ? <p className="muted">No bugs here yet.</p> : (
            <ul className="bugs">
              {bugs.map((b) => (
                <BugRow key={b.id} bug={b} users={users} me={me} token={token} onChanged={load} />
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}

// ---- App root ----
function App() {
  const [session, setSession] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem("session")); } catch { return null; }
  });
  function login(data) {
    sessionStorage.setItem("session", JSON.stringify(data));
    setSession(data);
  }
  function logout() {
    sessionStorage.removeItem("session");
    setSession(null);
  }
  return session ? <Dashboard session={session} onLogout={logout} /> : <AuthScreen onLogin={login} />;
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
