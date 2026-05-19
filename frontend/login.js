/* =============================================================
   login.js  –  KisanConnect Login / Register Page Logic
   =============================================================
   Talks to the FastAPI backend at http://localhost:8000
   Stores the logged-in username in sessionStorage so that
   index.html can read it and redirect back to login if missing.
   ============================================================= */

const API = 'http://localhost:8000';

// ── Tab switcher ──────────────────────────────────────────────
function switchTab(tab) {
    ['login', 'register'].forEach(t => {
        document.getElementById(`tab-${t}`).classList.toggle('active', t === tab);
        document.getElementById(`panel-${t}`).classList.toggle('active', t === tab);
    });
    clearAlerts();
}

// ── Password eye toggle ───────────────────────────────────────
function toggleEye(inputId, btnId) {
    const input = document.getElementById(inputId);
    const btn   = document.getElementById(btnId);
    const show  = input.type === 'password';
    input.type  = show ? 'text' : 'password';
    btn.textContent = show ? '🙈' : '👁';
}

// ── Alert helpers ─────────────────────────────────────────────
function showAlert(id, message, type) {
    const el = document.getElementById(id);
    el.textContent = (type === 'error' ? '⚠️  ' : '✅  ') + message;
    el.className = `alert ${type}`;
}

function clearAlerts() {
    ['login-alert', 'reg-alert'].forEach(id => {
        const el = document.getElementById(id);
        el.className = 'alert';
        el.textContent = '';
    });
}

// ── Spinner helpers ───────────────────────────────────────────
function setLoading(prefix, loading) {
    document.getElementById(`${prefix}-btn`).disabled    = loading;
    document.getElementById(`${prefix}-spinner`).style.display = loading ? 'block' : 'none';
    document.getElementById(`${prefix}-btn-text`).style.opacity = loading ? 0.5 : 1;
}

// ── LOGIN ─────────────────────────────────────────────────────
document.getElementById('login-form').addEventListener('submit', async function (e) {
    e.preventDefault();
    clearAlerts();

    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    if (!username || !password) {
        showAlert('login-alert', 'Please fill in all fields.', 'error');
        return;
    }

    setLoading('login', true);
    try {
        const res = await fetch(`${API}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });

        const data = await res.json();

        if (!res.ok) {
            showAlert('login-alert', data.detail || 'Login failed.', 'error');
            return;
        }

        // ── Store session & redirect ──────────────────────────
        sessionStorage.setItem('kc_user', data.username);
        showAlert('login-alert', 'Login successful! Redirecting…', 'success');
        setTimeout(() => { window.location.href = 'index.html'; }, 900);

    } catch (err) {
        showAlert('login-alert', 'Cannot reach backend. Is the server running?', 'error');
    } finally {
        setLoading('login', false);
    }
});

// ── REGISTER ──────────────────────────────────────────────────
document.getElementById('register-form').addEventListener('submit', async function (e) {
    e.preventDefault();
    clearAlerts();

    const username = document.getElementById('reg-username').value.trim();
    const email    = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;

    if (!username || !email || !password) {
        showAlert('reg-alert', 'Please fill in all fields.', 'error');
        return;
    }
    if (username.length < 3) {
        showAlert('reg-alert', 'Username must be at least 3 characters.', 'error');
        return;
    }
    if (password.length < 6) {
        showAlert('reg-alert', 'Password must be at least 6 characters.', 'error');
        return;
    }

    setLoading('reg', true);
    try {
        const res = await fetch(`${API}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password }),
        });

        const data = await res.json();

        if (!res.ok) {
            showAlert('reg-alert', data.detail || 'Registration failed.', 'error');
            return;
        }

        showAlert('reg-alert', 'Account created! Please log in.', 'success');
        document.getElementById('register-form').reset();
        setTimeout(() => switchTab('login'), 1500);

    } catch (err) {
        showAlert('reg-alert', 'Cannot reach backend. Is the server running?', 'error');
    } finally {
        setLoading('reg', false);
    }
});

// ── If already logged in, skip straight to app ────────────────
(function () {
    if (sessionStorage.getItem('kc_user')) {
        window.location.href = 'index.html';
    }
})();
