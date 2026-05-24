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
    page_title="Prijímačky",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# 2. APP SETTINGS
# ============================================================

APP_NAME = "Prijímačky"
APP_SUBTITLE = "príprava na prijímacie skúšky"

DAILY_GOAL = 130
REVIEW_DAYS_BEFORE_EXAM = 3
RECENT_LIMIT = 8
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
                padding-top: 1.8rem;
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
                border-radius: 28px;
                padding: 20px 24px;
                box-shadow: var(--shadow);
                margin-bottom: 18px;
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

            .hero-top-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 18px;
                flex-wrap: wrap;
            }

            .hero-kicker {
                color: #a78bfa;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                margin-bottom: 6px;
            }

            .hero-title {
                font-size: 30px;
                line-height: 1.05;
                font-weight: 900;
                letter-spacing: -0.055em;
                color: #ffffff;
                margin-bottom: 0;
            }

            .hero-pill-row {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                justify-content: flex-end;
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


            .sidebar-filter-note {
                color: #94a3b8;
                font-size: 12px;
                line-height: 1.45;
                padding: 6px 2px 12px 2px;
            }

            .sidebar-bottom-spacer {
                height: 22px;
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



            .sidebar-mini-note {
                color: #94a3b8;
                font-size: 12px;
                line-height: 1.5;
                margin: 8px 0 14px 0;
                padding: 10px 12px;
                border-radius: 14px;
                background: rgba(15, 23, 42, 0.52);
                border: 1px solid rgba(255,255,255,0.06);
            }

            .plan-row {
                display: flex;
                justify-content: space-between;
                gap: 10px;
                padding: 6px 0;
                border-bottom: 1px solid rgba(255,255,255,0.06);
                font-size: 13px;
            }

            .plan-row:last-child {
                border-bottom: none;
            }

            .plan-label {
                color: #94a3b8;
            }

            .plan-value {
                color: #f8fafc;
                font-weight: 800;
            }

            .tutorial-card {
                max-width: 640px;
                margin: 0 auto 18px auto;
                padding: 18px 18px;
                border-radius: 24px;
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.70));
                border: 1px solid rgba(255,255,255,0.10);
                box-shadow: 0 18px 46px rgba(0,0,0,0.28);
                position: relative;
                overflow: hidden;
            }

            .tutorial-card::before {
                content: "";
                position: absolute;
                width: 180px;
                height: 180px;
                right: -70px;
                top: -80px;
                border-radius: 999px;
                background: radial-gradient(circle, rgba(139,92,246,0.45), transparent 65%);
                animation: tutorialGlow 4s ease-in-out infinite alternate;
            }

            @keyframes tutorialGlow {
                from { transform: translateY(0) scale(1); opacity: 0.55; }
                to { transform: translateY(18px) scale(1.12); opacity: 0.95; }
            }

            .tutorial-title {
                color: #ffffff;
                font-weight: 900;
                font-size: 17px;
                letter-spacing: -0.02em;
                margin-bottom: 8px;
                position: relative;
                z-index: 1;
            }

            .tutorial-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                position: relative;
                z-index: 1;
            }

            .tutorial-step {
                padding: 11px 12px;
                border-radius: 16px;
                background: rgba(2, 6, 23, 0.44);
                border: 1px solid rgba(255,255,255,0.07);
                color: #cbd5e1;
                font-size: 12px;
                line-height: 1.45;
            }

            .tutorial-step strong {
                color: #f8fafc;
            }

            @media (max-width: 700px) {
                .tutorial-grid {
                    grid-template-columns: 1fr;
                }
            }



            .setup-lock-card {
                max-width: 760px;
                margin: 3rem auto 1.5rem auto;
                background:
                    linear-gradient(135deg, rgba(17, 24, 39, 0.98), rgba(30, 41, 59, 0.90));
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 32px;
                box-shadow: 0 24px 70px rgba(0,0,0,0.42);
                padding: 34px 36px;
                position: relative;
                overflow: hidden;
            }

            .setup-lock-card::before {
                content: "";
                position: absolute;
                inset: -1px;
                background:
                    radial-gradient(circle at 10% 0%, rgba(139,92,246,0.22), transparent 24rem),
                    radial-gradient(circle at 95% 20%, rgba(37,99,235,0.16), transparent 20rem);
                pointer-events: none;
            }

            .setup-lock-card > * {
                position: relative;
                z-index: 1;
            }

            .setup-lock-step {
                color: #a78bfa;
                font-size: 12px;
                font-weight: 850;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                margin-bottom: 10px;
            }

            .setup-lock-title {
                font-size: 34px;
                line-height: 1.06;
                font-weight: 900;
                letter-spacing: -0.055em;
                color: #ffffff;
                margin-bottom: 10px;
            }

            .setup-lock-text {
                color: #cbd5e1;
                font-size: 15px;
                line-height: 1.75;
            }

            .sidebar-setup-note {
                background: rgba(139, 92, 246, 0.12);
                border: 1px solid rgba(139, 92, 246, 0.28);
                border-radius: 18px;
                padding: 12px 13px;
                color: #ddd6fe;
                font-size: 12px;
                line-height: 1.55;
                margin: 10px 0 12px 0;
            }


            body.setup-active .stApp::after {
                content: "";
                position: fixed;
                inset: 0;
                background: rgba(2, 6, 23, 0.72);
                backdrop-filter: blur(3px);
                z-index: 9990;
                pointer-events: none;
            }

            body.setup-active section[data-testid="stSidebar"] {
                z-index: 10000 !important;
                position: relative !important;
            }

            .setup-focus-card {
                background:
                    linear-gradient(135deg, rgba(124, 58, 237, 0.22), rgba(37, 99, 235, 0.16)),
                    rgba(15, 23, 42, 0.96);
                border: 1px solid rgba(167, 139, 250, 0.38);
                border-radius: 20px;
                padding: 14px 15px;
                margin: 12px 0;
                box-shadow: 0 18px 50px rgba(0,0,0,0.45);
                position: relative;
                z-index: 10002;
            }

            .setup-focus-kicker {
                color: #a78bfa;
                font-size: 11px;
                font-weight: 850;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                margin-bottom: 6px;
            }

            .setup-focus-title {
                color: #ffffff;
                font-size: 17px;
                font-weight: 900;
                letter-spacing: -0.035em;
                margin-bottom: 4px;
            }

            .setup-focus-text {
                color: #cbd5e1;
                font-size: 12px;
                line-height: 1.55;
            }

            .setup-main-hint {
                position: fixed;
                left: 50%;
                top: 50%;
                transform: translate(-35%, -50%);
                max-width: 440px;
                background:
                    linear-gradient(135deg, rgba(17, 24, 39, 0.98), rgba(30, 41, 59, 0.94));
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 28px;
                padding: 24px 26px;
                box-shadow: 0 24px 80px rgba(0,0,0,0.55);
                z-index: 10001;
                pointer-events: none;
            }

            .setup-main-hint-step {
                color: #a78bfa;
                font-size: 12px;
                font-weight: 850;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                margin-bottom: 9px;
            }

            .setup-main-hint-title {
                color: #ffffff;
                font-size: 27px;
                line-height: 1.08;
                font-weight: 900;
                letter-spacing: -0.055em;
                margin-bottom: 8px;
            }

            .setup-main-hint-text {
                color: #cbd5e1;
                font-size: 14px;
                line-height: 1.7;
            }

            .setup-focused-widget {
                position: relative;
                z-index: 10003 !important;
                background: rgba(15, 23, 42, 0.98);
                border-radius: 18px;
                padding: 10px;
                border: 1px solid rgba(167,139,250,0.38);
                box-shadow: 0 18px 50px rgba(0,0,0,0.45);
                margin-bottom: 10px;
            }

            body.setup-active .main .block-container {
                pointer-events: none;
            }

            @media (max-width: 900px) {
                .hero-title {
                    font-size: 26px;
                }

                .top-hero {
                    padding: 20px 18px;
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
    prefix="prep_app_dark_v3/",
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
        "exam_dates",
        "loaded_user",
        "answered",
        "selected_field_index",
        "selected_subject_name",
        "setup_step",
        "setup_field_name",
        "setup_subject_name",
        "setup_completed"
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
        f"""
        <div class="login-card">
            <div class="hero-kicker">{escape(APP_NAME)}</div>
            <div class="login-title">Vitaj späť.</div>
            <div class="login-subtitle">
                Prihlás sa a pokračuj v príprave presne tam, kde si skončil.
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
                placeholder="zadaj používateľské meno"
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
        st.markdown(
            """
            <div class="tutorial-card">
                <div class="tutorial-title">Ako aplikácia funguje</div>
                <div class="tutorial-grid">
                    <div class="tutorial-step"><strong>Smart review</strong><br>Appka mieša nové, problémové a opakovacie otázky podľa tvojho progresu.</div>
                    <div class="tutorial-step"><strong>Celky</strong><br>Vieš sa učiť celý predmet alebo iba konkrétny tematický celok.</div>
                    <div class="tutorial-step"><strong>Termín skúšky</strong><br>Pre každý odbor si nastavíš vlastný dátum a appka vypočíta odporúčané tempo.</div>
                    <div class="tutorial-step"><strong>Len nesprávne</strong><br>Samostatný tréning otázok, ktoré si už pokazil. Počíta sa do aktivity, nie do nových otázok.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form("register_form"):
            display_name = st.text_input(
                "Meno",
                placeholder="Tvoje meno"
            )

            new_username = st.text_input(
                "Používateľské meno",
                placeholder="meno_pouzivatela"
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
        "exam_dates": {},
        "setup_completed": False,
        "last_settings": {
            "field_idx": 0,
            "subj_name": None,
            "topic_name": "Všetky celky",
            "study_mode": "Smart review"
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

    if "exam_dates" not in user_state:
        user_state["exam_dates"] = {}

    if "setup_completed" not in user_state:
        user_state["setup_completed"] = False

    if "last_settings" not in user_state:
        user_state["last_settings"] = {
            "field_idx": 0,
            "subj_name": None,
            "topic_name": "Všetky celky",
            "study_mode": "Smart review"
        }

    if "topic_name" not in user_state["last_settings"]:
        user_state["last_settings"]["topic_name"] = "Všetky celky"

    if "study_mode" not in user_state["last_settings"]:
        user_state["last_settings"]["study_mode"] = "Smart review"

    return user_state


def save_user_state(username, user_state):
    path = get_user_progress_path(username)
    write_json_file(path, user_state)


def save_progress():
    username = st.session_state.username

    user_state = {
        "subjects_data": st.session_state.subjects_data,
        "exam_dates": st.session_state.get("exam_dates", {}),
        "setup_completed": st.session_state.get("setup_completed", False),
        "last_settings": {
            "field_idx": st.session_state.selected_field_index,
            "subj_name": st.session_state.selected_subject_name,
            "topic_name": st.session_state.get("selected_topic_name", "Všetky celky"),
            "study_mode": st.session_state.get("study_mode", "Smart review")
        }
    }

    save_user_state(username, user_state)


if st.session_state.get("loaded_user") != st.session_state.username:
    loaded_state = load_user_state(st.session_state.username)

    st.session_state.subjects_data = loaded_state.get("subjects_data", {})
    st.session_state.exam_dates = loaded_state.get("exam_dates", {})
    st.session_state.setup_completed = loaded_state.get("setup_completed", False)
    st.session_state.last_settings = loaded_state.get(
        "last_settings",
        {
            "field_idx": 0,
            "subj_name": None,
            "topic_name": "Všetky celky",
            "study_mode": "Smart review"
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
        "new_seen": 0,
        "smart_answered": 0,
        "wrong_review_answered": 0
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

    stats = subject_state["daily_stats"][d]
    for key, value in default_daily_stats().items():
        if key not in stats:
            stats[key] = value

    return stats


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


def question_priority(q, subject_state, counts, final_review_period=False):
    qid = get_qid(q)
    p = get_question_progress(subject_state, qid)
    stats = get_daily_stats(subject_state)

    status = p.get("status", "NEW")
    score = 0
    today = date.today()
    next_review = parse_date_safe(p.get("next_review"))
    last_seen = parse_date_safe(p.get("last_seen"))

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
        if final_review_period:
            score -= 100
        elif stats.get("new_seen", 0) >= new_limit:
            score -= 70
        else:
            score += 30

    if final_review_period:
        if status != "MASTERED":
            score += 60
        else:
            score += 10

    return score


def choose_next_question(questions, subject_state, final_review_period=False):
    counts = count_statuses(subject_state, questions)
    recent_ids = subject_state.get("recent_question_ids", [])

    candidates = []

    for q in questions:
        qid = get_qid(q)
        p = get_question_progress(subject_state, qid)

        if p.get("status") == "MASTERED" and not final_review_period:
            continue

        priority = question_priority(q, subject_state, counts, final_review_period)
        candidates.append((priority, q))

    if not candidates:
        candidates = [(question_priority(q, subject_state, counts, final_review_period), q) for q in questions]

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



def sanitize_key(value):
    value = str(value)
    value = value.lower()
    value = re.sub(r"[^a-z0-9áäčďéíĺľňóôŕšťúýž]+", "_", value)
    value = value.strip("_")
    return value or "all"


def get_question_topic(q):
    topic = q.get("topic")

    if isinstance(topic, str) and topic.strip():
        return topic.strip()

    return "Nezaradené"


def get_available_topics(questions):
    topics = sorted({get_question_topic(q) for q in questions})
    return ["Všetky celky"] + topics


def filter_questions_by_topic(questions, selected_topic):
    if selected_topic == "Všetky celky":
        return questions

    return [q for q in questions if get_question_topic(q) == selected_topic]


def count_topic_questions(questions, selected_topic):
    if selected_topic == "Všetky celky":
        return len(questions)

    return sum(1 for q in questions if get_question_topic(q) == selected_topic)


def update_recent_questions(subject_state, qid):
    recent = subject_state.get("recent_question_ids", [])
    recent.append(str(qid))
    recent = recent[-RECENT_LIMIT:]
    subject_state["recent_question_ids"] = recent


def update_progress_after_answer(subject_state, qid, is_correct, study_mode="Smart review"):
    p = get_question_progress(subject_state, qid)
    stats = get_daily_stats(subject_state)

    old_status = p.get("status", "NEW")
    today = date.today()
    today_iso = today.isoformat()

    if p.get("first_seen") is None:
        p["first_seen"] = today_iso

    if old_status == "NEW" and study_mode == "Smart review":
        stats["new_seen"] += 1

    stats["answered"] += 1
    if study_mode == "Len nesprávne":
        stats["wrong_review_answered"] += 1
    else:
        stats["smart_answered"] += 1

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
            p["next_review"] = (today + timedelta(days=REVIEW_DAYS_BEFORE_EXAM)).isoformat()

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




def is_final_review_period(field_name):
    exam_dates = st.session_state.get("exam_dates", {})
    exam_date_raw = exam_dates.get(field_name)

    if not exam_date_raw:
        return False

    exam_date = parse_date_safe(exam_date_raw)

    if exam_date is None:
        return False

    days_until_exam = (exam_date - date.today()).days
    return 0 <= days_until_exam <= REVIEW_DAYS_BEFORE_EXAM


def calculate_recommended_daily_goal(field_name):
    """
    Vypočíta odporúčaný denný cieľ pre aktuálny odbor.
    Berie do úvahy:
    - termín skúšky používateľa,
    - posledné 3 dni ako rezervu na opakovanie,
    - počet otázok, ktoré ešte nie sú MASTERED vo všetkých predmetoch odboru.
    """
    exam_dates = st.session_state.get("exam_dates", {})
    exam_date_raw = exam_dates.get(field_name)

    if not exam_date_raw:
        return DAILY_GOAL, {}

    exam_date = parse_date_safe(exam_date_raw)

    if exam_date is None:
        return DAILY_GOAL, {}

    days_until_exam = (exam_date - date.today()).days
    learning_days = max(1, days_until_exam - REVIEW_DAYS_BEFORE_EXAM)

    recommended_by_subject = {}
    total_recommended = 0

    for subject_name, file_name in FIELDS.get(field_name, {}).items():
        subject_questions = load_questions(file_name)

        if not subject_questions:
            continue

        subject_state = st.session_state.subjects_data.get(
            file_name,
            {
                "progress": {},
                "daily_stats": {},
                "recent_question_ids": [],
                "score": 0,
                "total_count": len(subject_questions)
            }
        )

        remaining = 0

        for question in subject_questions:
            qid = get_qid(question)
            progress = get_question_progress(subject_state, qid)

            if progress.get("status", "NEW") != "MASTERED":
                remaining += 1

        recommended = int((remaining + learning_days - 1) // learning_days)
        recommended_by_subject[subject_name] = recommended
        total_recommended += recommended

    return max(DAILY_GOAL, total_recommended), recommended_by_subject


def calculate_learning_percent(subject_state, questions):
    if not questions:
        return 0

    weights = {
        "NEW": 0.0,
        "RED": 0.0,
        "YELLOW": 0.35,
        "GREEN": 0.70,
        "MASTERED": 1.0
    }

    total_score = 0.0

    for q in questions:
        qid = get_qid(q)
        p = get_question_progress(subject_state, qid)
        total_score += weights.get(p.get("status", "NEW"), 0.0)

    return round((total_score / len(questions)) * 100)


# ============================================================
# 8B. EXAM PLAN + STUDY MODES
# ============================================================

def get_exam_date_for_field(field_name):
    raw = st.session_state.get("exam_dates", {}).get(field_name)
    parsed = parse_date_safe(raw)
    return parsed


def set_exam_date_for_field(field_name, exam_date):
    if "exam_dates" not in st.session_state:
        st.session_state.exam_dates = {}

    if exam_date is None:
        st.session_state.exam_dates.pop(field_name, None)
    else:
        st.session_state.exam_dates[field_name] = exam_date.isoformat()

    save_progress()


def days_until_exam(exam_date):
    if exam_date is None:
        return None

    return (exam_date - date.today()).days


def is_final_review_window(exam_date):
    days_left = days_until_exam(exam_date)
    return days_left is not None and 0 <= days_left <= REVIEW_DAYS_BEFORE_EXAM


def get_unmastered_count(subject_state, questions):
    counts = count_statuses(subject_state, questions)
    return (
        counts.get("NEW", 0)
        + counts.get("RED", 0)
        + counts.get("YELLOW", 0)
        + counts.get("GREEN", 0)
    )


def calculate_field_plan(field_name, exam_date):
    result = {
        "days_left": None,
        "learning_days": None,
        "total_daily_needed": 0,
        "subjects": []
    }

    if exam_date is None:
        return result

    days_left = max(0, days_until_exam(exam_date))
    learning_days = max(0, days_left - REVIEW_DAYS_BEFORE_EXAM)

    result["days_left"] = days_left
    result["learning_days"] = learning_days

    subjects = FIELDS.get(field_name, {})

    for subject_name, file_name in subjects.items():
        subject_questions = load_questions(file_name)

        if not subject_questions:
            continue

        subject_state = ensure_subject_state(file_name, subject_questions)
        remaining = get_unmastered_count(subject_state, subject_questions)

        if learning_days > 0:
            daily_needed = (remaining + learning_days - 1) // learning_days
        else:
            daily_needed = 0

        result["subjects"].append({
            "subject": subject_name,
            "file": file_name,
            "remaining": remaining,
            "daily_needed": daily_needed,
            "total": len(subject_questions)
        })

        result["total_daily_needed"] += daily_needed

    return result


def get_dynamic_daily_goal(field_name, exam_date):
    plan = calculate_field_plan(field_name, exam_date)
    return max(DAILY_GOAL, plan.get("total_daily_needed", 0)), plan


def filter_questions_for_study_mode(questions, subject_state, study_mode, exam_date):
    if study_mode == "Len nesprávne":
        wrong_questions = []

        for q in questions:
            p = get_question_progress(subject_state, get_qid(q))
            if p.get("wrong_count", 0) > 0 or p.get("status") in ["RED", "YELLOW"]:
                wrong_questions.append(q)

        return wrong_questions

    if is_final_review_window(exam_date):
        review_questions = []

        for q in questions:
            p = get_question_progress(subject_state, get_qid(q))
            if p.get("status") != "NEW":
                review_questions.append(q)

        if review_questions:
            return review_questions

    return questions


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


def render_hero(
    subject_name,
    field_name,
    topic_name="Všetky celky",
    question_count=None,
    total_count=None,
    learning_percent=0,
    daily_goal=None
):
    if topic_name == "Všetky celky":
        subtitle = f"{field_name} · všetky celky"
    else:
        subtitle = f"{field_name} · {topic_name}"

    if question_count is not None and total_count is not None and question_count != total_count:
        count_label = f"{question_count} otázok vo výbere"
    elif question_count is not None:
        count_label = f"{question_count} otázok"
    else:
        count_label = f"Cieľ {daily_goal or DAILY_GOAL}/deň"

    display_daily_goal = daily_goal or DAILY_GOAL

    st.markdown(
        f"""
        <div class="top-hero">
            <div class="hero-top-row">
                <div>
                    <div class="hero-kicker">Smart review</div>
                    <div class="hero-title">{escape(subject_name)}</div>
                    <div style="color:#94a3b8;font-size:13px;margin-top:6px;">
                        {escape(subtitle)} · {escape(count_label)}
                    </div>
                </div>
                <div class="hero-pill-row">
                    <span class="hero-pill">Naučené: {learning_percent}%</span>
                    <span class="hero-pill">Cieľ: {display_daily_goal}/deň</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_question_header(q, p):
    st.markdown(
        f"""
        <div class="question-topline">
            <div class="question-number">Otázka č. {escape(str(q["id"]))}</div>
        </div>

        <div class="subtle-stats">
            Správne: {p.get("correct_count", 0)}
            &nbsp;·&nbsp;
            Nesprávne: {p.get("wrong_count", 0)}
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



def render_plan_rows(plan):
    subjects = plan.get("subjects", [])

    if not subjects:
        st.caption("Nastav termín skúšky a appka vypočíta denný plán podľa zostávajúcich otázok.")
        return

    for item in subjects:
        st.markdown(
            f"""
            <div class="plan-row">
                <span class="plan-label">{escape(item['subject'])}</span>
                <span class="plan-value">{item['daily_needed']} / deň</span>
            </div>
            """,
            unsafe_allow_html=True
        )


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
# 10. SPOTLIGHT SETUP
# ============================================================

def setup_is_active():
    return not st.session_state.get("setup_completed", False)


def setup_current_step():
    if "setup_step" not in st.session_state:
        st.session_state.setup_step = 1
    return st.session_state.setup_step


def setup_overlay(step, title, text):
    if not setup_is_active():
        return

    st.markdown(
        f"""
        <script>
            document.body.classList.add("setup-active");
        </script>
        <div class="setup-main-hint">
            <div class="setup-main-hint-step">Krok {step}/3</div>
            <div class="setup-main-hint-title">{escape(title)}</div>
            <div class="setup-main-hint-text">{escape(text)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def setup_sidebar_note(step, title, text):
    st.sidebar.markdown(
        f"""
        <div class="setup-focus-card">
            <div class="setup-focus-kicker">Krok {step}/3</div>
            <div class="setup-focus-title">{escape(title)}</div>
            <div class="setup-focus-text">{escape(text)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def begin_focused_widget():
    st.sidebar.markdown('<div class="setup-focused-widget">', unsafe_allow_html=True)


def end_focused_widget():
    st.sidebar.markdown('</div>', unsafe_allow_html=True)


def complete_setup_if_ready():
    field_list = list(FIELDS.keys())
    field_idx = st.session_state.get("selected_field_index", 0)

    if field_idx >= len(field_list):
        return

    field_name = field_list[field_idx]
    subject_name = st.session_state.get("selected_subject_name")

    if field_name and subject_name and st.session_state.get("exam_dates", {}).get(field_name):
        st.session_state.setup_completed = True
        st.session_state.setup_step = 4
        save_progress()
        st.rerun()


# ============================================================
# 11. SIDEBAR SETTINGS
# ============================================================

st.sidebar.markdown(
    f"""
    <div style="padding-bottom: 8px;">
        <div style="font-size: 22px; font-weight: 850; letter-spacing: -0.04em; color: #f9fafb;">
            {escape(APP_NAME)}
        </div>
        <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">
            {escape(APP_SUBTITLE)}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

setup_active = setup_is_active()
step = setup_current_step()

field_list = list(FIELDS.keys())
f_idx = st.session_state.last_settings.get("field_idx", 0)

if setup_active and step == 1:
    setup_sidebar_note(1, "Vyber si odbor", "Najprv vyber odbor. Ostatné nastavenia sa odomknú potom.")
    begin_focused_widget()

selected_field_name = st.sidebar.selectbox(
    "Odbor",
    field_list,
    index=f_idx if f_idx < len(field_list) else 0,
    disabled=setup_active and step != 1
)

if setup_active and step == 1:
    end_focused_widget()

st.session_state.selected_field_index = field_list.index(selected_field_name)

if setup_active and step == 1:
    if st.sidebar.button("Potvrdiť odbor", use_container_width=True):
        st.session_state.setup_step = 2
        save_progress()
        st.rerun()

    setup_overlay(
        1,
        "Vyber si odbor",
        "V sidebare je zvýraznený výber odboru. Najprv ho potvrď, potom sa odomkne termín skúšky."
    )

available_subjects = FIELDS[selected_field_name]
subj_list = list(available_subjects.keys())
default_subj = st.session_state.last_settings.get("subj_name")
s_idx = subj_list.index(default_subj) if default_subj in subj_list else 0

if "exam_dates" not in st.session_state:
    st.session_state.exam_dates = {}

if setup_active and step == 2:
    setup_sidebar_note(2, "Zadaj termín skúšky", "Termín použijeme na výpočet denného plánu.")
    begin_focused_widget()

current_exam_raw = st.session_state.exam_dates.get(selected_field_name)
current_exam_date = parse_date_safe(current_exam_raw) or date.today() + timedelta(days=21)

selected_exam_date = st.sidebar.date_input(
    "Termín skúšky",
    value=current_exam_date,
    disabled=setup_active and step != 2
)

if setup_active and step == 2:
    end_focused_widget()

if selected_exam_date:
    st.session_state.exam_dates[selected_field_name] = selected_exam_date.isoformat()

if setup_active and step == 2:
    if st.sidebar.button("Potvrdiť termín", use_container_width=True):
        save_progress()
        st.session_state.setup_step = 3
        st.rerun()

    setup_overlay(
        2,
        "Zadaj termín skúšky",
        "Vyber dátum prijímačiek. Aplikácia podľa neho vypočíta, koľko otázok denne treba prejsť."
    )

if setup_active and step == 3:
    setup_sidebar_note(3, "Vyber predmet", "Vyber predmet, ktorým chceš začať. Neskôr ho môžeš meniť.")
    begin_focused_widget()

st.session_state.selected_subject_name = st.sidebar.selectbox(
    "Predmet",
    subj_list,
    index=s_idx,
    disabled=setup_active and step != 3
)

if setup_active and step == 3:
    end_focused_widget()

if setup_active and step == 3:
    if st.sidebar.button("Začať testovať", use_container_width=True):
        st.session_state.last_settings["field_idx"] = st.session_state.selected_field_index
        st.session_state.last_settings["subj_name"] = st.session_state.selected_subject_name
        st.session_state.setup_completed = True
        save_progress()
        st.rerun()

    setup_overlay(
        3,
        "Vyber predmet",
        "Po výbere predmetu klikni na Začať testovať. Potom už bude aplikácia fungovať normálne."
    )

# Po dokončení setupu pokračuje normálna navigácia.
selected_file = available_subjects[st.session_state.selected_subject_name]
questions = load_questions(selected_file)

if not questions:
    dynamic_daily_goal = DAILY_GOAL

    render_hero(
        st.session_state.selected_subject_name,
        selected_field_name
    )

    st.error(f"Nepodarilo sa načítať súbor: {selected_file}")

    st.sidebar.divider()
    st.sidebar.caption(f"Prihlásený: {st.session_state.display_name}")

    if st.sidebar.button("Odhlásiť sa", use_container_width=True):
        logout_user()

    st.stop()

current_data = ensure_subject_state(selected_file, questions)

dynamic_daily_goal, recommended_by_subject = calculate_recommended_daily_goal(selected_field_name)
subject_daily_goal = max(1, recommended_by_subject.get(st.session_state.selected_subject_name, dynamic_daily_goal))
final_review_period = is_final_review_period(selected_field_name)
dynamic_new_goal = 0 if final_review_period else subject_daily_goal

topic_options = get_available_topics(questions)
default_topic = st.session_state.last_settings.get("topic_name", "Všetky celky")
t_idx = topic_options.index(default_topic) if default_topic in topic_options else 0

st.session_state.selected_topic_name = st.sidebar.selectbox(
    "Celok",
    topic_options,
    index=t_idx
)

study_modes = ["Smart review", "Len nesprávne"]
default_mode = st.session_state.last_settings.get("study_mode", "Smart review")
mode_idx = study_modes.index(default_mode) if default_mode in study_modes else 0

st.session_state.study_mode = st.sidebar.selectbox(
    "Režim",
    study_modes,
    index=mode_idx
)

current_exam_date = get_exam_date_for_field(selected_field_name)
default_exam_date = current_exam_date if current_exam_date else date(2026, 6, 12)
selected_exam_date = st.sidebar.date_input(
    "Termín skúšky",
    value=default_exam_date,
    format="DD.MM.YYYY"
)

if current_exam_date != selected_exam_date:
    set_exam_date_for_field(selected_field_name, selected_exam_date)
    current_exam_date = selected_exam_date

filtered_questions = filter_questions_by_topic(
    questions,
    st.session_state.selected_topic_name
)

mode_filtered_questions = filter_questions_for_study_mode(
    filtered_questions,
    current_data,
    st.session_state.study_mode,
    current_exam_date
)

if not filtered_questions:
    st.warning("V tomto celku zatiaľ nie sú žiadne otázky.")
    st.stop()

if not mode_filtered_questions:
    if st.session_state.study_mode == "Len nesprávne":
        st.warning("V tomto výbere zatiaľ nemáš žiadne nesprávne otázky. Prepni režim na Smart review.")
    else:
        st.warning("V tomto výbere momentálne nie sú otázky na opakovanie. Prepni celok alebo režim.")
    st.stop()

active_filter_key = f"{selected_file}::{st.session_state.selected_topic_name}::{st.session_state.study_mode}::{current_exam_date}"

if st.session_state.get("active_filter_key") != active_filter_key:
    st.session_state.answered = False
    st.session_state.active_filter_key = active_filter_key

st.sidebar.markdown(
    f"""
    <div class="sidebar-mini-note">
        Výber: <strong>{len(mode_filtered_questions)}</strong> otázok<br>
        Predmet spolu: {len(questions)} otázok
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 11. CURRENT QUESTION
# ============================================================

topic_key = sanitize_key(st.session_state.selected_topic_name)
mode_key = sanitize_key(st.session_state.study_mode)
question_session_key = f"current_question_id_{selected_file}_{topic_key}_{mode_key}"
nonce_key = f"answer_nonce_{selected_file}_{topic_key}_{mode_key}"

if nonce_key not in st.session_state:
    st.session_state[nonce_key] = 0

if question_session_key not in st.session_state:
    selected_question = choose_next_question(mode_filtered_questions, current_data)
    st.session_state[question_session_key] = get_qid(selected_question)

q = get_question_by_id(mode_filtered_questions, st.session_state[question_session_key])

if q is None:
    selected_question = choose_next_question(mode_filtered_questions, current_data)
    st.session_state[question_session_key] = get_qid(selected_question)
    q = selected_question

qid = get_qid(q)
q_progress = get_question_progress(current_data, qid)

if "answered" not in st.session_state:
    st.session_state.answered = False


# ============================================================
# 12. MAIN LAYOUT
# ============================================================



subject_learning_percent = calculate_learning_percent(current_data, questions)
hero_daily_goal, _hero_field_plan = get_dynamic_daily_goal(selected_field_name, current_exam_date)

render_hero(
    st.session_state.selected_subject_name,
    selected_field_name,
    st.session_state.selected_topic_name,
    len(mode_filtered_questions),
    len(questions),
    subject_learning_percent,
    hero_daily_goal
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

                update_progress_after_answer(current_data, qid, is_correct, st.session_state.study_mode)

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
    counts = count_statuses(current_data, mode_filtered_questions)
    daily_stats = get_daily_stats(current_data)
    new_limit = dynamic_daily_new_limit(counts)
    dynamic_new_goal = 0 if final_review_period else subject_daily_goal

    answered_today = daily_stats.get("answered", 0)
    new_seen_today = daily_stats.get("new_seen", 0)
    correct_today = daily_stats.get("correct", 0)
    wrong_today = daily_stats.get("wrong", 0)
    smart_today = daily_stats.get("smart_answered", 0)
    wrong_review_today = daily_stats.get("wrong_review_answered", 0)

    dynamic_daily_goal, field_plan = get_dynamic_daily_goal(selected_field_name, current_exam_date)
    days_left = field_plan.get("days_left")
    learning_days = field_plan.get("learning_days")

    not_mastered = (
        counts.get("NEW", 0)
        + counts.get("RED", 0)
        + counts.get("YELLOW", 0)
        + counts.get("GREEN", 0)
    )

    with st.container(border=True):
        st.markdown("### Dnes")
        metric_col_1, metric_col_2 = st.columns(2)
        metric_col_1.metric("Správne", correct_today)
        metric_col_2.metric("Nesprávne", wrong_today)
        st.caption(f"Smart review: {smart_today} · Len nesprávne: {wrong_review_today}")

    with st.container(border=True):
        st.markdown("### Denný cieľ")

        st.progress(progress_percent(answered_today, subject_daily_goal))
        st.markdown(f"**{answered_today} / {subject_daily_goal}** otázok dnes")

        if answered_today >= subject_daily_goal:
            st.success("Denný cieľ splnený.")
        else:
            st.caption(f"Zostáva dnes: {max(0, subject_daily_goal - answered_today)} otázok")

        st.divider()

        if dynamic_new_goal == 0:
            st.caption("Nové otázky dnes: vypnuté")
        else:
            st.caption(f"Nové otázky dnes: {new_seen_today} / {dynamic_new_goal}")
        if st.session_state.study_mode == "Len nesprávne":
            st.caption("Tento režim sa počíta do otázok dnes, ale nie do nových otázok.")

    with st.container(border=True):
        st.markdown("### Stav celku" if st.session_state.selected_topic_name != "Všetky celky" else "### Stav predmetu")

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

    if len(mode_filtered_questions) > 0 and counts.get("MASTERED", 0) == len(mode_filtered_questions):
        st.balloons()
        if st.session_state.selected_topic_name == "Všetky celky":
            st.success("Všetky otázky v tomto predmete sú zvládnuté.")
        else:
            st.success("Všetky otázky v tomto celku sú zvládnuté.")

        if st.button("Reštartovať predmet", use_container_width=True):
            if selected_file in st.session_state.subjects_data:
                del st.session_state.subjects_data[selected_file]

            if question_session_key in st.session_state:
                del st.session_state[question_session_key]

            save_progress()
            st.rerun()


    with st.expander("Plán do skúšky", expanded=False):
        if current_exam_date:
            st.markdown(f"**Termín:** {current_exam_date.strftime('%d.%m.%Y')}")
            st.caption(f"Zostáva dní: {days_left} · dni na nové otázky: {learning_days}")
            st.divider()
            render_plan_rows(field_plan)
            st.divider()
            st.caption(f"Minimum podľa termínu: {field_plan.get('total_daily_needed', 0)} otázok/deň")
        else:
            st.caption("Nastav termín skúšky v sidebare a appka vypočíta plán podľa predmetov.")


# ============================================================
# 13. SIDEBAR LOGOUT
# ============================================================

st.sidebar.markdown('<div class="sidebar-bottom-spacer"></div>', unsafe_allow_html=True)
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
