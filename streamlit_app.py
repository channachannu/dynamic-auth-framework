"""
streamlit_app.py
=================
DAF Phase 1 — Stakeholder Demo UI

Uses Supabase REST API (HTTPS) — works on Streamlit Cloud free tier.
No direct PostgreSQL connection needed.

Architecture:
    Streamlit Cloud
         ↓  HTTPS
    Supabase REST API
         ↓
    PostgreSQL (managed by Supabase)
"""

import hmac
import os
from datetime import datetime, timezone

import streamlit as st
from supabase import create_client, Client
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

# ---------------------------------------------------------------------------
# DPP Core Logic
# ---------------------------------------------------------------------------
_HASHER = PasswordHasher(time_cost=3, memory_cost=65_536, parallelism=4, hash_len=32)
DEFAULT_PLACEHOLDER = "x"


def _build_parameter_map(password, placeholder):
    return "".join("1" if ch == placeholder else "0" for ch in password)

def _extract_static_part(password, parameter_map):
    return "".join(ch for ch, flag in zip(password, parameter_map) if flag == "0")

def _extract_dynamic_part(password, parameter_map):
    return "".join(ch for ch, flag in zip(password, parameter_map) if flag == "1")

def _get_current_time_parameter():
    return datetime.now(tz=timezone.utc).strftime("%H%M")

def _secure_compare(a, b):
    return hmac.compare_digest(a.encode(), b.encode())

def dpp_register(password, placeholder=DEFAULT_PLACEHOLDER):
    """Register — returns (static_hash, parameter_map)."""
    if not password:
        raise ValueError("Password must not be empty.")
    if len(placeholder) != 1:
        raise ValueError("Placeholder must be exactly one character.")
    if all(ch == placeholder for ch in password):
        raise ValueError("Password must contain at least one static character.")
    parameter_map = _build_parameter_map(password, placeholder)
    static_part   = _extract_static_part(password, parameter_map)
    static_hash   = _HASHER.hash(static_part)
    return static_hash, parameter_map

def dpp_authenticate(input_password, stored_hash, parameter_map):
    """Two-stage DPP authentication — returns True/False."""
    if len(input_password) != len(parameter_map):
        return False
    dynamic_part = _extract_dynamic_part(input_password, parameter_map)
    live_dynamic = _get_current_time_parameter()
    if not _secure_compare(dynamic_part, live_dynamic):
        return False
    static_part = _extract_static_part(input_password, parameter_map)
    try:
        _HASHER.verify(stored_hash, static_part)
        return True
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# ---------------------------------------------------------------------------
# Supabase client
# ---------------------------------------------------------------------------
@st.cache_resource
def get_supabase() -> Client:
    """Create and cache the Supabase client."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
    return create_client(url, key)


# ---------------------------------------------------------------------------
# Database operations via Supabase REST API
# ---------------------------------------------------------------------------

def db_user_exists(username: str) -> bool:
    """Check if username already exists."""
    supabase = get_supabase()
    result = supabase.table("daf_users") \
        .select("id") \
        .eq("username", username) \
        .execute()
    return len(result.data) > 0


def db_create_user(username: str, static_hash: str, parameter_map: str, placeholder: str):
    """Insert a new user into daf_users."""
    supabase = get_supabase()
    supabase.table("daf_users").insert({
        "username":      username,
        "static_hash":   static_hash,
        "parameter_map": parameter_map,
        "placeholder":   placeholder,
        "is_active":     True,
    }).execute()


def db_get_user(username: str) -> dict | None:
    """Fetch a user by username."""
    supabase = get_supabase()
    result = supabase.table("daf_users") \
        .select("*") \
        .eq("username", username) \
        .execute()
    return result.data[0] if result.data else None


# ---------------------------------------------------------------------------
# Test connection on startup
# ---------------------------------------------------------------------------
try:
    get_supabase().table("daf_users").select("id").limit(1).execute()
except Exception as e:
    st.error(f"❌ Supabase connection failed: {e}")
    st.stop()


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
    utc_now = datetime.now(tz=timezone.utc)
    hhmm    = utc_now.strftime("%H%M")
    st.metric("Current UTC", utc_now.strftime("%H:%M:%S"))
    st.info(f"Dynamic value now: **{hhmm}**")
    if st.button("🔄 Refresh Clock"):
        st.rerun()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_reg, tab_auth, tab_how = st.tabs([
    "📝 Register", "🔑 Authenticate", "📖 How It Works"
])

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
        password    = st.text_input(
            "Password", placeholder="e.g. Botxxnetxx", type="password")
        show        = st.checkbox("Show password")
        if show and password:
            st.code(password)
        placeholder = st.text_input(
            "Placeholder character", value="x", max_chars=1)
        submitted   = st.form_submit_button("Register", use_container_width=True)

    if submitted:
        if not username or not password:
            st.error("Username and password are required.")
        else:
            with st.spinner("Registering..."):
                try:
                    if db_user_exists(username):
                        st.markdown(
                            '<div class="error-card">❌ Username already taken.</div>',
                            unsafe_allow_html=True)
                    else:
                        static_hash, parameter_map = dpp_register(password, placeholder)
                        db_create_user(username, static_hash, parameter_map, placeholder)

                        st.markdown(
                            '<div class="success-card">✅ <b>Registration successful!</b></div>',
                            unsafe_allow_html=True)

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Password Length",   len(parameter_map))
                        col2.metric("Static positions",  parameter_map.count("0"))
                        col3.metric("Dynamic positions", parameter_map.count("1"))

                        st.markdown(f"**Parameter map:** `{parameter_map}`")
                        st.info(
                            f"At current UTC **{hhmm}**, fill your `{placeholder}` "
                            f"positions with the current time digits."
                        )
                        st.session_state["registered_user"] = username

                except ValueError as e:
                    st.markdown(
                        f'<div class="error-card">❌ {str(e)}</div>',
                        unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

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
                    user = db_get_user(auth_user)

                    if not user:
                        st.markdown(
                            '<div class="error-card">❌ <b>Invalid credentials.</b></div>',
                            unsafe_allow_html=True)
                    elif not user["is_active"]:
                        st.markdown(
                            '<div class="error-card">❌ <b>Account is inactive.</b></div>',
                            unsafe_allow_html=True)
                    else:
                        success = dpp_authenticate(
                            input_password=auth_pass,
                            stored_hash=user["static_hash"],
                            parameter_map=user["parameter_map"],
                        )
                        if success:
                            st.markdown(
                                '<div class="success-card">✅ <b>Authentication successful!</b>'
                                '<br>Both dynamic and static stages verified.</div>',
                                unsafe_allow_html=True)
                            col1, col2 = st.columns(2)
                            col1.metric("Stage 1 — Dynamic", "✅ Passed")
                            col2.metric("Stage 2 — Static",  "✅ Passed")
                        else:
                            st.markdown(
                                '<div class="error-card">❌ <b>Authentication failed.</b>'
                                '<br>Check your dynamic positions match current UTC time.</div>',
                                unsafe_allow_html=True)
                            col1, col2 = st.columns(2)
                            col1.metric("Stage 1 — Dynamic", "❌ Failed")
                            col2.metric("Stage 2 — Static",  "—")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ── HOW IT WORKS ─────────────────────────────────────────────────────────────
with tab_how:
    st.markdown("#### How the Dynamic Password Protocol Works")

    col1, col2, col3 = st.columns(3)
    col1.markdown("**Registration**"); col1.code("Botxxnetxx")
    col2.markdown("**Placeholder**");  col2.code("x")
    col3.markdown("**Parameter Map**"); col3.code("0001100011")

    st.markdown("---")
    st.markdown("**Login examples with pattern `Botxxnetxx`:**")
    st.table({
        "UTC Time":       ["21:30", "21:31", "22:30"],
        "Login Password": ["Bot21net30", "Bot21net31", "Bot22net30"],
        "Valid?":         ["✅ Yes", "✅ Yes", "✅ Yes"],
    })

    st.markdown("---")
    st.markdown("**Two-stage verification:**")
    st.markdown("""
    1. **Stage 1 — Dynamic** — extracted digits must match current UTC time
    2. **Stage 2 — Static** — extracted letters must match stored Argon2id hash

    Both stages must pass. All failures return a **generic message**.
    """)

    st.markdown("---")
    st.markdown("**Security:**")
    st.table({
        "Attack":      ["Replay", "Brute Force", "Phishing", "DB Breach"],
        "DPP Defence": [
            "Password expires every 60s",
            "Argon2id — 64MB RAM per attempt",
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
    "Supabase + Streamlit Cloud"
)
