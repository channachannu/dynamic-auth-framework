"""
streamlit_app.py
=================
DAF Phase 1 — Stakeholder Demo UI.

Run:
    streamlit run streamlit_app.py

Requirements:
    FastAPI must be running → uvicorn main:app --reload
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from datetime import datetime, timezone
import streamlit as st

API_BASE = "http://localhost:8000/v1/auth"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Dynamic Auth Framework",
    page_icon="🔐",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0D1B2A 0%, #1B4F8A 100%);
        padding: 2rem; border-radius: 12px;
        text-align: center; margin-bottom: 2rem;
    }
    .main-header h1 { color: white; font-size: 2rem; margin: 0; }
    .main-header p  { color: #D6EAF8; margin: 0.5rem 0 0 0; }
    .success-card {
        background: #D5F5E3; border-left: 4px solid #1E8449;
        padding: 1rem; border-radius: 6px; margin: 1rem 0;
    }
    .error-card {
        background: #FADBD8; border-left: 4px solid #C0392B;
        padding: 1rem; border-radius: 6px; margin: 1rem 0;
    }
    .info-card {
        background: #F2F3F4; border-left: 4px solid #1B4F8A;
        padding: 1rem; border-radius: 6px; margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🔐 Dynamic Auth Framework</h1>
    <p>Dynamic Password Protocol — Phase 1 POC Demo</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### About DAF")
    st.markdown("""
    **Dynamic Auth Framework** is built on the **Dynamic Password Protocol (DPP)**.

    A password has two parts:
    - 🟢 **Static** — characters you remember
    - 🔴 **Dynamic** — filled by live UTC time

    **Example:**
    - Register: `Botxxnetxx`
    - At 21:30 UTC → login: `Bot21net30`
    - At 21:31 UTC → login: `Bot21net31`

    A stolen password expires in **60 seconds**.

    ---
    *H. Channabasava & S. Kanthimathi*
    *CompCom 2019, Springer Nature*
    """)

    st.markdown("---")
    st.markdown("### 🕐 Live UTC Time")
    utc_now  = datetime.now(tz=timezone.utc)
    hhmm     = utc_now.strftime("%H%M")
    st.metric("Current UTC", utc_now.strftime("%H:%M:%S"))
    st.info(f"Dynamic value now: **{hhmm}**")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_reg, tab_auth, tab_how = st.tabs(["📝 Register", "🔑 Authenticate", "📖 How It Works"])

# ── REGISTER ─────────────────────────────────────────────────────────────────
with tab_reg:
    st.markdown("#### Create a DAF Account")
    st.markdown("""
    <div class="info-card">
    Use a placeholder character (default: <b>x</b>) to mark dynamic positions
    in your password. These will be filled by the UTC time at login.
    </div>
    """, unsafe_allow_html=True)

    with st.form("register_form"):
        username    = st.text_input("Username", placeholder="e.g. Botnet")
        password    = st.text_input("Password", placeholder="e.g. Botxxnetxx", type="password")
        show        = st.checkbox("Show password")
        if show and password:
            st.code(password)
        placeholder = st.text_input("Placeholder character", value="x", max_chars=1)
        submitted   = st.form_submit_button("Register", use_container_width=True)

    if submitted:
        if not username or not password:
            st.error("Username and password are required.")
        else:
            with st.spinner("Registering..."):
                try:
                    res = requests.post(
                        f"{API_BASE}/register",
                        json={"username": username, "password": password, "placeholder": placeholder},
                        timeout=10,
                    )
                    if res.status_code == 201:
                        data = res.json()
                        pmap = data["parameter_map"]
                        st.markdown('<div class="success-card">✅ <b>Registration successful!</b></div>',
                                    unsafe_allow_html=True)

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Password Length", len(pmap))
                        col2.metric("Static positions",  pmap.count("0"))
                        col3.metric("Dynamic positions", pmap.count("1"))

                        st.markdown(f"**Parameter map:** `{pmap}`")
                        st.info(f"At current UTC **{hhmm}**, fill your `{placeholder}` positions with `{hhmm[:pmap.count('1')]}`")

                        st.session_state["registered_user"] = username
                    else:
                        try:
                            detail = res.json().get("detail", "Registration failed.")
                        except Exception:
                            detail = f"Registration failed. (HTTP {res.status_code})"
                        st.markdown(f'<div class="error-card">❌ {detail}</div>', unsafe_allow_html=True)

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to DAF API. Is FastAPI running on port 8000?")

# ── AUTHENTICATE ─────────────────────────────────────────────────────────────
with tab_auth:
    st.markdown("#### Authenticate with Your Dynamic Password")
    st.markdown("""
    <div class="info-card">
    Fill the dynamic positions with the <b>current UTC time (HHMM)</b>.
    Check the live clock in the sidebar.
    </div>
    """, unsafe_allow_html=True)

    hhmm_now = datetime.now(tz=timezone.utc).strftime("%H%M")
    st.info(f"⏱ Current dynamic value: **{hhmm_now}**")

    with st.form("auth_form"):
        auth_user = st.text_input(
            "Username",
            value=st.session_state.get("registered_user", ""),
            placeholder="e.g. Botnet",
        )
        auth_pass = st.text_input(
            "Password",
            placeholder=f"e.g. Bot{hhmm_now[:2]}net{hhmm_now[2:]}",
            type="password",
        )
        show_auth = st.checkbox("Show password")
        if show_auth and auth_pass:
            st.code(auth_pass)
        auth_sub = st.form_submit_button("Authenticate", use_container_width=True)

    if auth_sub:
        if not auth_user or not auth_pass:
            st.error("Username and password are required.")
        else:
            with st.spinner("Verifying..."):
                try:
                    res = requests.post(
                        f"{API_BASE}/authenticate",
                        json={"username": auth_user, "password": auth_pass},
                        timeout=10,
                    )
                    if res.status_code == 200:
                        st.markdown('<div class="success-card">✅ <b>Authentication successful!</b><br>Both dynamic and static stages verified.</div>',
                                    unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        col1.metric("Stage 1 — Dynamic", "✅ Passed")
                        col2.metric("Stage 2 — Static",  "✅ Passed")
                    else:
                        st.markdown('<div class="error-card">❌ <b>Authentication failed.</b><br>Check your dynamic positions match current UTC time.</div>',
                                    unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        col1.metric("Stage 1 — Dynamic", "❌ Failed")
                        col2.metric("Stage 2 — Static",  "—")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to DAF API. Is FastAPI running on port 8000?")

# ── HOW IT WORKS ─────────────────────────────────────────────────────────────
with tab_how:
    st.markdown("#### How the Dynamic Password Protocol Works")

    col1, col2, col3 = st.columns(3)
    col1.markdown("**Registration**"); col1.code("Botxxnetxx")
    col2.markdown("**Placeholder**");  col2.code("x")
    col3.markdown("**Parameter Map**"); col3.code("0001100011")

    st.markdown("---")
    st.markdown("**Login examples:**")
    st.table({
        "UTC Time":       ["21:30", "21:31", "22:30"],
        "Login Password": ["Bot21net30", "Bot21net31", "Bot22net30"],
        "Valid?":         ["✅ Yes", "✅ Yes", "✅ Yes"],
    })

    st.markdown("---")
    st.markdown("**Security:**")
    st.table({
        "Attack":        ["Replay", "Brute Force", "Phishing", "DB Breach"],
        "DPP Defence":   [
            "Password expires every 60s",
            "Argon2id — ~100ms per attempt",
            "Stolen password immediately stale",
            "Only hash + parameter map stored",
        ],
    })

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(
    "Dynamic Auth Framework — Phase 1 POC  |  "
    "H. Channabasava & S. Kanthimathi, CompCom 2019  |  "
    "FastAPI + PostgreSQL + Streamlit"
)