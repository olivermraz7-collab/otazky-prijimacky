import streamlit as st
import json
import re
import random
import os
import hashlib
import secrets
from datetime import date, timedelta
from html import escape
from streamlit_cookies_manager import EncryptedCookieManager


# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Medicína Príprava",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# 2. APP SETTINGS
# ============================================================

DAILY_GOAL = 130
RECENT_LIMIT = 8
FINAL_MODE_DATE = date(2026, 6, 10)

DATA_DIR = "data"
PROGRESS_DIR = os.path.join(DATA_DIR, "progress")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

REPORT_FORM_BASE_URL = "https://docs.google.com/forms/d/e/1FAIpQLScVa1VK6mJYX6YRmgcms64AMxaTm5wSDmJF9vnl1M4QzzmCUw/viewform"

FIELDS = {
    "Všeobecné lekárstvo": {
        "Biológia": "biologia.json",
        "Chémia": "chemia.json"
    },
    "Urgentná medicína": {
        "Náuka o spoločnosti": "nos.json",
        "Fyzika": "fyzika.json",
        "Biológia": "biologia-urgent.json"
    }
}


# ============================================================
# 3. DARK PREMIUM CSS
# ============================================================

def inject_css():
    st.markdown(
        """
        <style>
            :root {
                --bg: #09090b;
                --bg-soft: #0f172a;
                --card: rgba(17, 24, 39, 0.88);
                --card-solid: #111827;
                --border: rgba(255, 255, 255, 0.08);
                --text: #f9fafb;
                --muted: #9ca3af;
                --primary: #8b5cf6;
                --primary-2: #3b82f6;
                --shadow: 0 24px 70px rgba(0, 0, 0, 0.42);
                --shadow-soft: 0 16px 40px rgba(0, 0, 0, 0.28);
            }

            html, body, .stApp {
                background:
                    radial-gradient(circle at top left, rgba(124, 58, 237, 0.22), transparent 34rem),
                    radial-gradient(circle at top right, rgba(37, 99, 235, 0.18), transparent 32rem),
                    linear-gradient(135deg, #09090b 0%, #0f172a 52%, #020617 100%) !important;
                color: var(--text) !important;
            }

            .block-container {
                padding-top: 2.2rem;
                padding-bottom: 3rem;
                max-width: 1240px;
            }

            h1, h2, h3, h4, h5, h6, p, span, label {
                color: var(--text);
            }

            section[data-testid="stSidebar"] {
                background: rgba(3, 7, 18, 0.72) !important;
                backdrop-filter: blur(24px);
                border-right: 1px solid var(--border);
            }

            section[data-testid="stSidebar"] > div {
                padding-top: 1.3rem;
            }

            .top-hero {
                background:
                    linear-gradient(135deg, rgba(17, 24, 39, 0.92), rgba(30, 41, 59, 0.78));
                border: 1px solid var(--border);
                border-radius: 30px;
                padding: 30px 32px;
                box-shadow: var(--shadow);
                margin-bottom: 22px;
                position: relative;
                overflow: hidden;
            }

            .top-hero::before {
                content: "";
                position: absolute;
                inset: -1px;
                background:
                    radial-gradient(circle at 20% 0%, rgba(139, 92, 246, 0.22), transparent 24rem),
                    radial-gradient(circle at 90% 20%, rgba(59, 130, 246, 0.18), transparent 20rem);
                pointer-events: none;
            }

            .top-hero > * {
                position: relative;
                z-index: 1;
            }

            .hero-kicker {
                color: #a78bfa;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                margin-bottom: 10px;
            }

            .hero-title {
                font-size: 38px;
                line-height: 1.02;
                font-weight: 900;
                letter-spacing: -0.055em;
                color: #ffffff;
                margin-bottom: 10px;
            }

            .hero-subtitle {
                color: #cbd5e1;
                font-size: 15px;
                line-height: 1.65;
                max-width: 780px;
            }

            .hero-pill-row {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: 20px;
            }

            .hero-pill {
                display: inline-flex;
                align-items: center;
                padding: 8px 12px;
                border-radius: 999px;
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.10);
                color: #e5e7eb;
                font-size: 12px;
                font-weight: 700;
            }

            .question-topline {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 14px;
                margin-bottom: 12px;
                flex-wrap: wrap;
            }

            .question-number {
                color: #ffffff;
                font-weight: 900;
                font-size: 24px;
                letter-spacing: -0.035em;
            }

            .subtle-stats {
                color: #94a3b8;
                font-size: 12px;
                line-height: 1.8;
                margin-bottom: 16px;
            }

            .question-text {
                font-size: 17px;
                line-height: 1.75;
                color: #f8fafc;
                margin-bottom: 10px;
            }

            .status-pill {
                display: inline-flex;
                align-items: center;
                border-radius: 999px;
                padding: 7px 11px;
                font-size: 12px;
                font-weight: 800;
                border: 1px solid transparent;
            }

            .status-new {
                background: rgba(148, 163, 184, 0.14);
                color: #cbd5e1;
                border-color: rgba(148, 163, 184, 0.22);
            }

            .status-red {
                background: rgba(248, 113, 113, 0.14);
                color: #fecaca;
                border-color: rgba(248, 113, 113, 0.28);
            }

            .status-yellow {
                background: rgba(250, 204, 21, 0.14);
                color: #fde68a;
                border-color: rgba(250, 204, 21, 0.25);
            }

            .status-green {
                background: rgba(74, 222, 128, 0.14);
                color: #bbf7d0;
                border-color: rgba(74, 222, 128, 0.25);
            }

            .status-mastered {
                background: rgba(139, 92, 246, 0.18);
                color: #ddd6fe;
                border-color: rgba(139, 92, 246, 0.34);
            }

            .tiny-report {
                text-align: right;
                margin-top: 10px;
                margin-bottom: 4px;
            }

            .tiny-report a {
                color: #64748b;
                text-decoration: none;
                font-size: 12px;
                transition: color 0.15s ease;
            }

            .tiny-report a:hover {
                color: #cbd5e1;
                text-decoration: underline;
            }

            .footer-user {
                font-size: 12px;
                color: #94a3b8;
                margin-top: 8px;
            }

            .login-card {
                max-width: 640px;
                margin: 3rem auto 1.5rem auto;
                background:
                    linear-gradient(135deg, rgba(17, 24, 39, 0.96), rgba(30, 41, 59, 0.88));
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 32px;
                box-shadow: var(--shadow);
                padding: 36px 38px;
            }

            .login-title {
                font-size: 36px;
                line-height: 1.05;
                font-weight: 900;
                letter-spacing: -0.055em;
                color: #ffffff;
                margin-bottom: 10px;
            }

            .login-subtitle {
                font-size: 14px;
                color: #cbd5e1;
                line-height: 1.7;
                margin-bottom: 18px;
            }

            .warning-box {
                background: rgba(250, 204, 21, 0.12);
                border: 1px solid rgba(250, 204, 21, 0.28);
                color: #fde68a;
                padding: 13px 15px;
                border-radius: 16px;
                font-size: 14px;
                margin: 10px 0;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: linear-gradient(180deg, rgba(17, 24, 39, 0.92), rgba(15, 23, 42, 0.88)) !important;
                border: 1px solid rgba(255,255,255,0.08) !important;
                border-radius: 26px !important;
                box-shadow: 0 16px 40px rgba(0,0,0,0.28) !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] > div {
                padding: 8px 10px !important;
            }

            div.stButton > button,
            div.stFormSubmitButton > button {
                border-radius: 15px !important;
                border: 1px solid rgba(167, 139, 250, 0.30) !important;
                background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
                color: #ffffff !important;
                font-weight: 850 !important;
                padding: 0.70rem 1.1rem !important;
                box-shadow: 0 14px 32px rgba(124, 58, 237, 0.30) !important;
                transition: transform 0.12s ease, box-shadow 0.12s ease, filter 0.12s ease !important;
            }

            div.stButton > button:hover,
            div.stFormSubmitButton > button:hover {
                transform: translateY(-1px);
                filter: brightness(1.05);
                box-shadow: 0 18px 38px rgba(124, 58, 237, 0.38) !important;
            }

            div[data-testid="stTabs"] {
                max-width: 640px;
                margin: 0 auto;
                background: rgba(15, 23, 42, 0.72) !important;
                border: 1px solid rgba(255,255,255,0.09) !important;
                border-radius: 24px !important;
                padding: 16px !important;
                box-shadow: 0 20px 50px rgba(0,0,0,0.28) !important;
            }

            div[data-baseweb="tab-list"] {
                background: rgba(2, 6, 23, 0.65) !important;
                border-radius: 16px !important;
                padding: 5px !important;
                border: 1px solid rgba(255,255,255,0.08) !important;
                gap: 4px;
            }

            button[data-baseweb="tab"] {
                color: #94a3b8 !important;
                background: transparent !important;
                border-radius: 12px !important;
                font-weight: 800 !important;
                padding: 10px 14px !important;
            }

            button[data-baseweb="tab"] p {
                color: #94a3b8 !important;
                font-weight: 800 !important;
            }

            button[data-baseweb="tab"][aria-selected="true"] {
                background: linear-gradient(135deg, rgba(124,58,237,0.26), rgba(37,99,235,0.22)) !important;
                color: #ffffff !important;
                border: 1px solid rgba(167,139,250,0.25) !important;
            }

            button[data-baseweb="tab"][aria-selected="true"] p {
                color: #ffffff !important;
            }

            label,
            label p,
            div[data-testid="stTextInput"] label,
            div[data-testid="stTextInput"] label p,
            div[data-testid="stSelectbox"] label,
            div[data-testid="stSelectbox"] label p {
                color: #dbeafe !important;
                font-weight: 800 !important;
                font-size: 13px !important;
            }

            div[data-testid="stTextInput"] input {
                color: #f9fafb !important;
                background: rgba(2, 6, 23, 0.74) !important;
                border: 1px solid rgba(148, 163, 184, 0.22) !important;
                border-radius: 16px !important;
                min-height: 44px !important;
                box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02) !important;
            }

            div[data-testid="stTextInput"] input:focus {
                border-color: rgba(139, 92, 246, 0.75) !important;
                box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.20) !important;
            }

            div[data-testid="stTextInput"] input::placeholder {
                color: #64748b !important;
                opacity: 1 !important;
            }

            input[type="password"],
            input[type="text"] {
                color: #f9fafb !important;
                background-color: rgba(2, 6, 23, 0.74) !important;
            }

            div[data-baseweb="select"] > div {
                background: rgba(2, 6, 23, 0.74) !important;
                border: 1px solid rgba(148, 163, 184, 0.22) !important;
                border-radius: 16px !important;
                color: #f9fafb !important;
                min-height: 44px !important;
            }

            div[data-baseweb="select"] span {
                color: #f9fafb !important;
            }

            div[data-testid="stCheckbox"] {
                background: rgba(15, 23, 42, 0.72);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 16px;
                padding: 10px 13px;
                margin-bottom: 10px;
                transition: background 0.12s ease, border 0.12s ease, transform 0.12s ease;
            }

            div[data-testid="stCheckbox"]:hover {
                background: rgba(30, 41, 59, 0.80);
                border-color: rgba(139, 92, 246, 0.35);
                transform: translateY(-1px);
            }

            div[data-testid="stCheckbox"] label,
            div[data-testid="stCheckbox"] label p {
                color: #e5e7eb !important;
                font-weight: 550 !important;
            }

            div[data-testid="stMetricValue"] {
                color: #ffffff !important;
                font-size: 1.55rem;
            }

            div[data-testid="stMetricLabel"] {
                color: #94a3b8 !important;
            }

            .stProgress > div > div {
                background-color: rgba(255,255,255,0.08) !important;
            }

            .stProgress > div > div > div > div {
                background: linear-gradient(90deg, #7c3aed, #2563eb) !important;
            }

            div[data-testid="stAlert"] {
                background: rgba(15, 23, 42, 0.86) !important;
                border: 1px solid rgba(255,255,255,0.10) !important;
                border-radius: 18px !important;
                color: #f9fafb !important;
            }

            hr {
                border-color: rgba(255,255,255,0.08) !important;
            }

            @media (max-width: 900px) {
                .hero-title {
                    font-size: 29px;
                }

                .top-hero {
                    padding: 24px 22px;
                }

                .login-card {
                    padding: 28px 24px;
                }
            }
        </style>
        """,
        unsafe_allow_html=True
    )


inject_css()


# ============================================================
# 4. COOKIES - IBA LOGIN
# ============================================================

cookies = EncryptedCookieManager(
    prefix="med_prep_dark_v2/",
    password="Heslo1234"
)

if not cookies.ready():
    st.stop()


# ============================================================
# 5. FILE HELPERS
# ============================================================

def ensure_data_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PROGRESS_DIR, exist_ok=True)


ensure_data_dirs()


def read_json_file(path, default):
    try:
        if not os.path.exists(path):
            return default

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return default


def write_json_file(path, data):
    tmp_path = path + ".tmp"

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    os.replace(tmp_path, path)


# ============================================================
# 6. AUTH
# ============================================================

def normalize_username(username):
    username = username.strip().lower()
    username = re.sub(r"[^a-z0-9_.-]", "_", username)
    username = username.strip("._-")
    return username


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        150_000
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password, stored_hash):
    try:
        salt, correct_hash = stored_hash.split("$", 1)
        attempted_hash = hash_password(password, salt).split("$", 1)[1]
        return secrets.compare_digest(attempted_hash, correct_hash)

    except Exception:
        return False


def load_users():
    data = read_json_file(USERS_FILE, default={"users": {}})

    if "users" not in data:
        data = {"users": {}}

    return data


def save_users(data):
    write_json_file(USERS_FILE, data)


def create_user(username, display_name, password):
    username = normalize_username(username)

    if not username:
        return False, "Používateľské meno nemôže byť prázdne."

    if len(password) < 4:
        return False, "Heslo musí mať aspoň 4 znaky."

    users_data = load_users()

    if username in users_data["users"]:
        return False, "Tento používateľ už existuje."

    users_data["users"][username] = {
        "username": username,
        "display_name": display_name.strip() if display_name.strip() else username,
        "password_hash": hash_password(password)
    }

    save_users(users_data)

    return True, "Účet bol vytvorený."


def authenticate_user(username, password):
    username = normalize_username(username)
    users_data = load_users()
    user = users_data["users"].get(username)

    if not user:
        return None

    if not verify_password(password, user.get("password_hash", "")):
        return None

    return user


def get_logged_user_from_cookie():
    username = cookies.get("logged_in_user")

    if not username:
        return None

    username = normalize_username(username)
    users_data = load_users()

    if username in users_data["users"]:
        return users_data["users"][username]

    return None


def login_user(user):
    st.session_state.authenticated = True
    st.session_state.username = user["username"]
    st.session_state.display_name = user["display_name"]

    cookies["logged_in_user"] = user["username"]
    cookies.save()


def logout_user():
    cookies["logged_in_user"] = ""
    cookies.save()

    keys_to_delete = [
        "authenticated",
        "username",
        "display_name",
        "subjects_data",
        "last_settings",
        "loaded_user",
        "answered",
        "selected_field_index",
        "selected_subject_name"
    ]

    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]

    for key in list(st.session_state.keys()):
        if key.startswith("current_question_id_") or key.startswith("answer_nonce_"):
            del st.session_state[key]

    st.rerun()


def render_login_screen():
    st.markdown(
        """
        <div class="login-card">
            <div class="hero-kicker">Medicína Príprava</div>
            <div class="login-title">Vitaj späť.</div>
            <div class="login-subtitle">
                Prihlás sa a pokračuj presne tam, kde si skončil. Každý používateľ má vlastné otázky,
                vlastný progres a vlastný smart review systém.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    users_data = load_users()

    if len(users_data["users"]) == 0:
        st.markdown(
            """
            <div class="warning-box">
                Zatiaľ neexistuje žiadny používateľ. Vytvor si prvý účet v záložke Registrácia.
            </div>
            """,
            unsafe_allow_html=True
        )

    login_tab, register_tab = st.tabs(["Prihlásenie", "Registrácia"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input(
                "Používateľské meno",
                placeholder="napr. oliver"
            )

            password = st.text_input(
                "Heslo",
                type="password",
                placeholder="zadaj heslo"
            )

            submitted = st.form_submit_button("Prihlásiť sa")

        if submitted:
            user = authenticate_user(username, password)

            if user:
                login_user(user)
                st.rerun()
            else:
                st.error("Nesprávne používateľské meno alebo heslo.")

    with register_tab:
        with st.form("register_form"):
            display_name = st.text_input(
                "Meno",
                placeholder="napr. Oliver"
            )

            new_username = st.text_input(
                "Používateľské meno",
                placeholder="napr. oliver"
            )

            new_password = st.text_input(
                "Heslo",
                type="password",
                placeholder="minimálne 4 znaky"
            )

            new_password_confirm = st.text_input(
                "Zopakuj heslo",
                type="password",
                placeholder="zopakuj heslo"
            )

            submitted_register = st.form_submit_button("Vytvoriť účet")

        if submitted_register:
            if new_password != new_password_confirm:
                st.error("Heslá sa nezhodujú.")
            else:
                success, message = create_user(
                    new_username,
                    display_name,
                    new_password
                )

                if success:
                    user = authenticate_user(new_username, new_password)

                    if user:
                        login_user(user)
                        st.success(message)
                        st.rerun()
                else:
                    st.error(message)


if "authenticated" not in st.session_state:
    cookie_user = get_logged_user_from_cookie()

    if cookie_user:
        st.session_state.authenticated = True
        st.session_state.username = cookie_user["username"]
        st.session_state.display_name = cookie_user["display_name"]
    else:
        st.session_state.authenticated = False

if not st.session_state.authenticated:
    render_login_screen()
    st.stop()


# ============================================================
# 7. USER PROGRESS
# ============================================================

def get_user_progress_path(username):
    safe_username = normalize_username(username)
    return os.path.join(PROGRESS_DIR, f"{safe_username}.json")


def default_user_state():
    return {
        "subjects_data": {},
        "last_settings": {
            "field_idx": 0,
            "subj_name": None
        }
    }


def load_user_state(username):
    path = get_user_progress_path(username)
    user_state = read_json_file(path, default=None)

    if user_state is None:
        user_state = default_user_state()
        save_user_state(username, user_state)
        return user_state

    if "subjects_data" not in user_state:
        user_state["subjects_data"] = {}

    if "last_settings" not in user_state:
        user_state["last_settings"] = {
            "field_idx": 0,
            "subj_name": None
        }

    return user_state


def save_user_state(username, user_state):
    path = get_user_progress_path(username)
    write_json_file(path, user_state)


def save_progress():
    username = st.session_state.username

    user_state = {
        "subjects_data": st.session_state.subjects_data,
        "last_settings": {
            "field_idx": st.session_state.selected_field_index,
            "subj_name": st.session_state.selected_subject_name
        }
    }

    save_user_state(username, user_state)


if st.session_state.get("loaded_user") != st.session_state.username:
    loaded_state = load_user_state(st.session_state.username)

    st.session_state.subjects_data = loaded_state.get("subjects_data", {})
    st.session_state.last_settings = loaded_state.get(
        "last_settings",
        {
            "field_idx": 0,
            "subj_name": None
        }
    )

    st.session_state.loaded_user = st.session_state.username


# ============================================================
# 8. SMART REVIEW LOGIC
# ============================================================

def today_str():
    return date.today().isoformat()


def parse_date_safe(value):
    try:
        if not value:
            return None

        return date.fromisoformat(value)

    except Exception:
        return None


def load_questions(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return []


def get_qid(q):
    return str(q["id"])


def default_question_progress():
    return {
        "status": "NEW",
        "level": 0,
        "correct_count": 0,
        "wrong_count": 0,
        "streak": 0,
        "first_seen": None,
        "last_seen": None,
        "next_review": today_str(),
        "last_result": None
    }


def default_daily_stats():
    return {
        "answered": 0,
        "correct": 0,
        "wrong": 0,
        "new_seen": 0
    }


def ensure_subject_state(selected_file, questions):
    if selected_file not in st.session_state.subjects_data:
        st.session_state.subjects_data[selected_file] = {
            "score": 0,
            "total_count": len(questions),
            "progress": {},
            "daily_stats": {},
            "recent_question_ids": [],
            "smart_review_version": 1
        }

        save_progress()

    subject_state = st.session_state.subjects_data[selected_file]

    if "progress" not in subject_state:
        subject_state["progress"] = {}

    if "daily_stats" not in subject_state:
        subject_state["daily_stats"] = {}

    if "recent_question_ids" not in subject_state:
        subject_state["recent_question_ids"] = []

    if "total_count" not in subject_state:
        subject_state["total_count"] = len(questions)

    if "score" not in subject_state:
        subject_state["score"] = 0

    subject_state["smart_review_version"] = 1

    if "pool" in subject_state:
        del subject_state["pool"]

    return subject_state


def get_daily_stats(subject_state):
    d = today_str()

    if d not in subject_state["daily_stats"]:
        subject_state["daily_stats"][d] = default_daily_stats()

    return subject_state["daily_stats"][d]


def get_question_progress(subject_state, qid):
    progress = subject_state["progress"]

    if qid not in progress:
        progress[qid] = default_question_progress()

    p = progress[qid]

    defaults = default_question_progress()

    for key, value in defaults.items():
        if key not in p:
            p[key] = value

    return p


def count_statuses(subject_state, questions):
    counts = {
        "NEW": 0,
        "RED": 0,
        "YELLOW": 0,
        "GREEN": 0,
        "MASTERED": 0
    }

    for q in questions:
        qid = get_qid(q)
        p = get_question_progress(subject_state, qid)
        status = p.get("status", "NEW")

        if status not in counts:
            status = "NEW"

        counts[status] += 1

    return counts


def dynamic_daily_new_limit(counts):
    red_count = counts.get("RED", 0)

    if red_count >= 180:
        return 40

    if red_count >= 100:
        return 70

    if red_count >= 40:
        return 100

    return DAILY_GOAL


def question_priority(q, subject_state, counts):
    qid = get_qid(q)
    p = get_question_progress(subject_state, qid)
    stats = get_daily_stats(subject_state)

    status = p.get("status", "NEW")
    score = 0
    today = date.today()
    next_review = parse_date_safe(p.get("next_review"))
    last_seen = parse_date_safe(p.get("last_seen"))
    is_final_mode = today >= FINAL_MODE_DATE

    if status == "RED":
        score += 140
    elif status == "YELLOW":
        score += 95
    elif status == "GREEN":
        score += 45
    elif status == "NEW":
        score += 35
    elif status == "MASTERED":
        score -= 120

    score += p.get("wrong_count", 0) * 18

    if p.get("last_result") == "wrong":
        score += 20

    if next_review is not None and next_review <= today:
        score += 70

    if last_seen is None:
        score += 15
    else:
        days_ago = (today - last_seen).days

        if days_ago >= 7:
            score += 35
        elif days_ago >= 3:
            score += 20
        elif days_ago >= 1:
            score += 8

    new_limit = dynamic_daily_new_limit(counts)

    if status == "NEW":
        if stats.get("new_seen", 0) >= new_limit:
            score -= 70
        else:
            score += 30

    if is_final_mode:
        if status != "MASTERED":
            score += 60
        else:
            score += 10

    return score


def choose_next_question(questions, subject_state):
    counts = count_statuses(subject_state, questions)
    recent_ids = subject_state.get("recent_question_ids", [])

    candidates = []

    for q in questions:
        qid = get_qid(q)
        p = get_question_progress(subject_state, qid)

        if p.get("status") == "MASTERED" and date.today() < FINAL_MODE_DATE:
            continue

        priority = question_priority(q, subject_state, counts)
        candidates.append((priority, q))

    if not candidates:
        candidates = [(question_priority(q, subject_state, counts), q) for q in questions]

    filtered = [
        (priority, q)
        for priority, q in candidates
        if get_qid(q) not in recent_ids
    ]

    if len(filtered) >= 5:
        candidates = filtered

    candidates.sort(key=lambda item: item[0], reverse=True)

    top_n = min(12, len(candidates))
    top_candidates = candidates[:top_n]

    min_score = min(priority for priority, _ in top_candidates)
    weights = [max(1, priority - min_score + 1) for priority, _ in top_candidates]

    selected = random.choices(
        [q for _, q in top_candidates],
        weights=weights,
        k=1
    )[0]

    return selected


def get_question_by_id(questions, qid):
    for q in questions:
        if get_qid(q) == str(qid):
            return q

    return None


def update_recent_questions(subject_state, qid):
    recent = subject_state.get("recent_question_ids", [])
    recent.append(str(qid))
    recent = recent[-RECENT_LIMIT:]
    subject_state["recent_question_ids"] = recent


def update_progress_after_answer(subject_state, qid, is_correct):
    p = get_question_progress(subject_state, qid)
    stats = get_daily_stats(subject_state)

    old_status = p.get("status", "NEW")
    today = date.today()
    today_iso = today.isoformat()

    if p.get("first_seen") is None:
        p["first_seen"] = today_iso

    if old_status == "NEW":
        stats["new_seen"] += 1

    stats["answered"] += 1
    p["last_seen"] = today_iso

    if is_correct:
        stats["correct"] += 1

        p["correct_count"] += 1
        p["streak"] += 1
        p["last_result"] = "correct"

        if old_status == "RED":
            p["level"] = max(1, p.get("level", 0))
        else:
            p["level"] = min(4, p.get("level", 0) + 1)

        if p["level"] <= 1:
            p["status"] = "YELLOW"
            p["next_review"] = (today + timedelta(days=1)).isoformat()
        elif p["level"] == 2:
            p["status"] = "GREEN"
            p["next_review"] = (today + timedelta(days=3)).isoformat()
        elif p["level"] == 3:
            p["status"] = "GREEN"
            p["next_review"] = (today + timedelta(days=7)).isoformat()
        else:
            p["status"] = "MASTERED"
            p["next_review"] = FINAL_MODE_DATE.isoformat()

        if old_status == "NEW":
            subject_state["score"] = subject_state.get("score", 0) + 1

    else:
        stats["wrong"] += 1

        p["wrong_count"] += 1
        p["streak"] = 0
        p["level"] = 0
        p["status"] = "RED"
        p["last_result"] = "wrong"
        p["next_review"] = today_iso

    update_recent_questions(subject_state, qid)


def progress_percent(value, goal):
    if goal <= 0:
        return 0.0

    return min(1.0, value / goal)


# ============================================================
# 9. UI HELPERS
# ============================================================

def status_label(status):
    labels = {
        "NEW": "Nová",
        "RED": "Problémová",
        "YELLOW": "Na opakovanie",
        "GREEN": "Zvládnutá",
        "MASTERED": "Mastered"
    }

    return labels.get(status, status)


def status_class(status):
    classes = {
        "NEW": "status-new",
        "RED": "status-red",
        "YELLOW": "status-yellow",
        "GREEN": "status-green",
        "MASTERED": "status-mastered"
    }

    return classes.get(status, "status-new")


def render_hero(subject_name, field_name, display_name):
    st.markdown(
        f"""
        <div class="top-hero">
            <div class="hero-kicker">Smart review systém</div>
            <div class="hero-title">Príprava: {escape(subject_name)}</div>
            <div class="hero-subtitle">
                Personalizované opakovanie otázok podľa toho, čo ovládaš, čo si mýliš
                a čo je potrebné zopakovať. Každý používateľ má vlastný progres.
            </div>
            <div class="hero-pill-row">
                <span class="hero-pill">Odbor: {escape(field_name)}</span>
                <span class="hero-pill">Používateľ: {escape(display_name)}</span>
                <span class="hero-pill">Denný cieľ: {DAILY_GOAL} otázok</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_question_header(q, p):
    status = p.get("status", "NEW")
    next_review = p.get("next_review") or "—"

    st.markdown(
        f"""
        <div class="question-topline">
            <div class="question-number">Otázka č. {escape(str(q["id"]))}</div>
            <div class="status-pill {status_class(status)}">{escape(status_label(status))}</div>
        </div>

        <div class="subtle-stats">
            Správne: {p.get("correct_count", 0)}
            &nbsp;·&nbsp;
            Nesprávne: {p.get("wrong_count", 0)}
            &nbsp;·&nbsp;
            Ďalšie opakovanie: {escape(str(next_review))}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_small_report_link(q, subject_name):
    form_url = (
        f"{REPORT_FORM_BASE_URL}"
        f"?usp=pp_url"
        f"&entry.424182118={q['id']}"
        f"&entry.1513577736={subject_name}"
    )

    st.markdown(
        f"""
        <div class="tiny-report">
            <a href="{form_url}" target="_blank">Nahlásiť chybu</a>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_sidebar_card(title, rows):
    with st.sidebar.container(border=True):
        st.markdown(f"#### {title}")

        for label, value in rows:
            col1, col2 = st.columns([0.65, 0.35])
            col1.caption(str(label))
            col2.markdown(f"**{value}**")


def render_question_text_and_images(q):
    segments = re.split(r"(\S+\.png|\S+\.jpg)", q["text"])

    for segment in segments:
        clean_segment = segment.strip()

        if clean_segment.lower().endswith((".png", ".jpg")):
            try:
                st.image(f"images/{clean_segment}", width=340)
            except Exception:
                st.error(f"Obrázok {clean_segment} chýba.")
        else:
            if clean_segment:
                st.markdown(
                    f"""
                    <div class="question-text">
                        {escape(clean_segment)}
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# ============================================================
# 10. SIDEBAR SETTINGS
# ============================================================

st.sidebar.markdown(
    """
    <div style="padding-bottom: 8px;">
        <div style="font-size: 22px; font-weight: 850; letter-spacing: -0.04em; color: #f9fafb;">
            Medicína
        </div>
        <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">
            príprava na prijímačky
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

field_list = list(FIELDS.keys())
f_idx = st.session_state.last_settings.get("field_idx", 0)

selected_field_name = st.sidebar.selectbox(
    "Odbor",
    field_list,
    index=f_idx if f_idx < len(field_list) else 0
)

st.session_state.selected_field_index = field_list.index(selected_field_name)

available_subjects = FIELDS[selected_field_name]
subj_list = list(available_subjects.keys())
default_subj = st.session_state.last_settings.get("subj_name")
s_idx = subj_list.index(default_subj) if default_subj in subj_list else 0

st.session_state.selected_subject_name = st.sidebar.selectbox(
    "Predmet",
    subj_list,
    index=s_idx
)

selected_file = available_subjects[st.session_state.selected_subject_name]
questions = load_questions(selected_file)

if not questions:
    render_hero(
        st.session_state.selected_subject_name,
        selected_field_name,
        st.session_state.display_name
    )

    st.error(f"Nepodarilo sa načítať súbor: {selected_file}")

    st.sidebar.divider()
    st.sidebar.caption(f"Prihlásený: {st.session_state.display_name}")

    if st.sidebar.button("Odhlásiť sa", use_container_width=True):
        logout_user()

    st.stop()

current_data = ensure_subject_state(selected_file, questions)


# ============================================================
# 11. CURRENT QUESTION
# ============================================================

question_session_key = f"current_question_id_{selected_file}"
nonce_key = f"answer_nonce_{selected_file}"

if nonce_key not in st.session_state:
    st.session_state[nonce_key] = 0

if question_session_key not in st.session_state:
    selected_question = choose_next_question(questions, current_data)
    st.session_state[question_session_key] = get_qid(selected_question)

q = get_question_by_id(questions, st.session_state[question_session_key])

if q is None:
    selected_question = choose_next_question(questions, current_data)
    st.session_state[question_session_key] = get_qid(selected_question)
    q = selected_question

qid = get_qid(q)
q_progress = get_question_progress(current_data, qid)

if "answered" not in st.session_state:
    st.session_state.answered = False


# ============================================================
# 12. MAIN LAYOUT
# ============================================================

render_hero(
    st.session_state.selected_subject_name,
    selected_field_name,
    st.session_state.display_name
)

left_col, right_col = st.columns([0.70, 0.30], gap="large")


with left_col:
    with st.container(border=True):
        render_question_header(q, q_progress)
        render_question_text_and_images(q)

        user_choices = []

        st.divider()

        with st.form(key=f"form_{selected_file}_{q['id']}_{st.session_state[nonce_key]}"):
            for opt in q["options"]:
                match = re.search(r"(\S+\.png|\S+\.jpg)", opt, re.IGNORECASE)

                if match:
                    img_filename = match.group(1)
                    clean_label = opt.replace(img_filename, "").strip()

                    if len(clean_label) < 4:
                        clean_label = opt[:3]

                    cb = st.checkbox(
                        clean_label,
                        key=f"cb_{selected_file}_{q['id']}_{st.session_state[nonce_key]}_{opt}",
                        disabled=st.session_state.answered
                    )

                    try:
                        st.image(f"images/{img_filename}", width=260)
                    except Exception:
                        st.warning(f"Súbor {img_filename} chýba.")
                else:
                    cb = st.checkbox(
                        opt,
                        key=f"cb_{selected_file}_{q['id']}_{st.session_state[nonce_key]}_{opt}",
                        disabled=st.session_state.answered
                    )

                if cb:
                    user_choices.append(opt[0])

            btn_label = "Pokračovať" if st.session_state.answered else "Skontrolovať"
            submit = st.form_submit_button(btn_label)

        if submit:
            if not st.session_state.answered:
                st.session_state.answered = True
                st.rerun()

            else:
                user_str = "".join(sorted(user_choices))
                correct_str = "".join(sorted(q["answer"]))
                is_correct = user_str == correct_str

                update_progress_after_answer(current_data, qid, is_correct)

                if question_session_key in st.session_state:
                    del st.session_state[question_session_key]

                st.session_state[nonce_key] += 1
                st.session_state.answered = False

                save_progress()
                st.rerun()

        if st.session_state.answered:
            correct_display = ", ".join(q["answer"])
            user_str = "".join(sorted(user_choices))
            correct_str = "".join(sorted(q["answer"]))

            if user_str == correct_str:
                st.success(f"Správne. Odpoveď: {correct_display}")
            else:
                st.error(f"Nesprávne. Správna odpoveď: {correct_display}")

        render_small_report_link(q, st.session_state.selected_subject_name)


with right_col:
    counts = count_statuses(current_data, questions)
    daily_stats = get_daily_stats(current_data)
    new_limit = dynamic_daily_new_limit(counts)

    answered_today = daily_stats.get("answered", 0)
    new_seen_today = daily_stats.get("new_seen", 0)
    correct_today = daily_stats.get("correct", 0)
    wrong_today = daily_stats.get("wrong", 0)

    not_mastered = (
        counts.get("NEW", 0)
        + counts.get("RED", 0)
        + counts.get("YELLOW", 0)
        + counts.get("GREEN", 0)
    )

    with st.container(border=True):
        st.markdown("### Denný cieľ")
        st.progress(progress_percent(answered_today, DAILY_GOAL))
        st.markdown(f"**{answered_today} / {DAILY_GOAL}** otázok dnes")

        st.progress(progress_percent(new_seen_today, new_limit))
        st.markdown(f"**{new_seen_today} / {new_limit}** nových otázok")

        if answered_today >= DAILY_GOAL:
            st.success("Denný cieľ splnený.")
        else:
            st.caption(f"Zostáva dnes: {max(0, DAILY_GOAL - answered_today)} otázok")

    with st.container(border=True):
        st.markdown("### Dnes")
        metric_col_1, metric_col_2 = st.columns(2)
        metric_col_1.metric("Správne", correct_today)
        metric_col_2.metric("Nesprávne", wrong_today)

    with st.container(border=True):
        st.markdown("### Stav predmetu")

        status_rows = [
            ("Nové", counts.get("NEW", 0)),
            ("Problémové", counts.get("RED", 0)),
            ("Na opakovanie", counts.get("YELLOW", 0)),
            ("Zvládnuté", counts.get("GREEN", 0)),
            ("Mastered", counts.get("MASTERED", 0)),
            ("Zostáva zvládnuť", not_mastered)
        ]

        for label, value in status_rows:
            col1, col2 = st.columns([0.7, 0.3])
            col1.caption(label)
            col2.markdown(f"**{value}**")

    if len(questions) > 0 and counts.get("MASTERED", 0) == len(questions):
        st.balloons()
        st.success("Všetky otázky v tomto predmete sú zvládnuté.")

        if st.button("Reštartovať predmet", use_container_width=True):
            if selected_file in st.session_state.subjects_data:
                del st.session_state.subjects_data[selected_file]

            if question_session_key in st.session_state:
                del st.session_state[question_session_key]

            save_progress()
            st.rerun()


# ============================================================
# 13. SIDEBAR STATS + LOGOUT
# ============================================================

counts = count_statuses(current_data, questions)
daily_stats = get_daily_stats(current_data)
new_limit = dynamic_daily_new_limit(counts)

answered_today = daily_stats.get("answered", 0)
new_seen_today = daily_stats.get("new_seen", 0)

render_sidebar_card(
    "Rýchly prehľad",
    [
        ("Otázky dnes", f"{answered_today} / {DAILY_GOAL}"),
        ("Nové dnes", f"{new_seen_today} / {new_limit}"),
        ("Problémové", counts.get("RED", 0)),
        ("Mastered", counts.get("MASTERED", 0))
    ]
)

st.sidebar.divider()
st.sidebar.markdown(
    f"""
    <div class="footer-user">
        Prihlásený: <strong>{escape(st.session_state.display_name)}</strong>
    </div>
    """,
    unsafe_allow_html=True
)

if st.sidebar.button("Odhlásiť sa", use_container_width=True):
    logout_user()
