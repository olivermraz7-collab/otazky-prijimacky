import streamlit as st
import json
import re
import random
import os
import hashlib
import secrets
from datetime import date, timedelta
from streamlit_cookies_manager import EncryptedCookieManager

st.set_page_config(
    page_title="Medicína Príprava",
    layout="centered"
)

# ============================================================
# 1. NASTAVENIA
# ============================================================

DAILY_GOAL = 130
RECENT_LIMIT = 8
FINAL_MODE_DATE = date(2026, 6, 10)

DATA_DIR = "data"
PROGRESS_DIR = os.path.join(DATA_DIR, "progress")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

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

REPORT_FORM_BASE_URL = "https://docs.google.com/forms/d/e/1FAIpQLScVa1VK6mJYX6YRmgcms64AMxaTm5wSDmJF9vnl1M4QzzmCUw/viewform"


# ============================================================
# 2. COOKIES - IBA LOGIN
# ============================================================

cookies = EncryptedCookieManager(
    prefix="med_prep_v4/",
    password="Heslo1234"
)

if not cookies.ready():
    st.stop()


# ============================================================
# 3. PRIEČINKY A JSON FUNKCIE
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
# 4. LOGIN / REGISTRÁCIA
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
        "current_question_id",
        "selected_field_index",
        "selected_subject_name"
    ]

    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]

    st.rerun()


def render_login_screen():
    st.title("Medicína Príprava")

    users_data = load_users()

    if len(users_data["users"]) == 0:
        st.info("Zatiaľ neexistuje žiadny používateľ. Vytvor si prvý účet.")

    login_tab, register_tab = st.tabs(["Prihlásenie", "Registrácia"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Používateľské meno")
            password = st.text_input("Heslo", type="password")
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
            display_name = st.text_input("Meno")
            new_username = st.text_input("Používateľské meno")
            new_password = st.text_input("Heslo", type="password")
            new_password_confirm = st.text_input("Zopakuj heslo", type="password")
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
# 5. POUŽÍVATEĽSKÝ PROGRES
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
# 6. OTÁZKY A SMART REVIEW FUNKCIE
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
            data = json.load(f)
            return data

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

    weights = []
    min_score = min(priority for priority, _ in top_candidates)

    for priority, _ in top_candidates:
        weights.append(max(1, priority - min_score + 1))

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


def render_question_stats_above_question(p):
    status = p.get("status", "NEW")
    next_review = p.get("next_review") or "—"

    st.markdown(
        f"""
        <div style="
            font-size: 11px;
            color: #999;
            margin-top: 4px;
            margin-bottom: 6px;
            text-align: left;
        ">
            Stav: {status}
            &nbsp;·&nbsp; Správne: {p.get("correct_count", 0)}
            &nbsp;·&nbsp; Nesprávne: {p.get("wrong_count", 0)}
            &nbsp;·&nbsp; Opakovanie: {next_review}
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
        <div style="text-align: right; margin-top: 8px; margin-bottom: 4px;">
            <a href="{form_url}" target="_blank" style="
                font-size: 13px;
                color: #888;
                text-decoration: none;
            ">
                Nahlásiť chybu
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# 7. SIDEBAR A VÝBER PREDMETU
# ============================================================

st.sidebar.header("Nastavenia")

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
    st.title(f"Príprava: {st.session_state.selected_subject_name}")
    st.error(f"Nepodarilo sa načítať súbor: {selected_file}")

    st.sidebar.divider()
    st.sidebar.caption(f"Prihlásený: {st.session_state.display_name}")

    if st.sidebar.button("Odhlásiť sa", use_container_width=True):
        logout_user()

    st.stop()

current_data = ensure_subject_state(selected_file, questions)


# ============================================================
# 8. VÝBER AKTUÁLNEJ OTÁZKY
# ============================================================

question_session_key = f"current_question_id_{selected_file}"

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
# 9. HLAVNÉ TESTOVACIE ROZHRANIE
# ============================================================

st.title(f"Príprava: {st.session_state.selected_subject_name}")

render_question_stats_above_question(q_progress)

st.subheader(f"Otázka č. {q['id']}")

segments = re.split(r"(\S+\.png|\S+\.jpg)", q["text"])

for segment in segments:
    clean_segment = segment.strip()

    if clean_segment.lower().endswith((".png", ".jpg")):
        try:
            st.image(f"images/{clean_segment}", width=300)
        except Exception:
            st.error(f"Obrázok {clean_segment} chýba.")
    else:
        if clean_segment:
            st.write(clean_segment)

user_choices = []

with st.form(key=f"form_{selected_file}_{q['id']}"):
    for opt in q["options"]:
        match = re.search(r"(\S+\.png|\S+\.jpg)", opt, re.IGNORECASE)

        if match:
            img_filename = match.group(1)
            clean_label = opt.replace(img_filename, "").strip()

            if len(clean_label) < 4:
                clean_label = opt[:3]

            cb = st.checkbox(
                clean_label,
                key=f"cb_{selected_file}_{q['id']}_{opt}",
                disabled=st.session_state.answered
            )

            try:
                st.image(f"images/{img_filename}", width=250)
            except Exception:
                st.warning(f"Súbor {img_filename} chýba.")
        else:
            cb = st.checkbox(
                opt,
                key=f"cb_{selected_file}_{q['id']}_{opt}",
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

        for opt in q["options"]:
            checkbox_key = f"cb_{selected_file}_{q['id']}_{opt}"

            if checkbox_key in st.session_state:
                del st.session_state[checkbox_key]

        if question_session_key in st.session_state:
            del st.session_state[question_session_key]

        st.session_state.answered = False

        save_progress()
        st.rerun()

if st.session_state.answered:
    correct_display = ", ".join(q["answer"])
    user_str = "".join(sorted(user_choices))
    correct_str = "".join(sorted(q["answer"]))

    if user_str == correct_str:
        st.success(f"✅ Správne! Odpoveď: {correct_display}")
    else:
        st.error(f"❌ Nesprávne! Správna odpoveď: {correct_display}")

render_small_report_link(q, st.session_state.selected_subject_name)


# ============================================================
# 10. SIDEBAR ŠTATISTIKY A MOTIVÁCIA
# ============================================================

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

st.sidebar.divider()
st.sidebar.write("🎯 Denný progres")
st.sidebar.progress(progress_percent(answered_today, DAILY_GOAL))
st.sidebar.write(f"Otázky dnes: **{answered_today} / {DAILY_GOAL}**")

st.sidebar.progress(progress_percent(new_seen_today, new_limit))
st.sidebar.write(f"Nové dnes: **{new_seen_today} / {new_limit}**")

if answered_today >= DAILY_GOAL:
    st.sidebar.success("Denný cieľ splnený ✅")
else:
    st.sidebar.caption(f"Zostáva dnes: {max(0, DAILY_GOAL - answered_today)} otázok")

st.sidebar.divider()
st.sidebar.write("📊 Stav otázok")
st.sidebar.write(f"Nové: **{counts.get('NEW', 0)}**")
st.sidebar.write(f"Problémové: **{counts.get('RED', 0)}**")
st.sidebar.write(f"Na opakovanie: **{counts.get('YELLOW', 0)}**")
st.sidebar.write(f"Zvládnuté: **{counts.get('GREEN', 0)}**")
st.sidebar.write(f"Mastered: **{counts.get('MASTERED', 0)}**")
st.sidebar.write(f"Zostáva zvládnuť: **{not_mastered}**")

st.sidebar.divider()
st.sidebar.write("Dnes")
st.sidebar.write(f"Správne: **{correct_today}**")
st.sidebar.write(f"Nesprávne: **{wrong_today}**")

if len(questions) > 0 and counts.get("MASTERED", 0) == len(questions):
    st.balloons()
    st.success("Hotovo! Všetky otázky v tomto predmete sú MASTERED.")

    if st.sidebar.button("Reštartovať predmet"):
        if selected_file in st.session_state.subjects_data:
            del st.session_state.subjects_data[selected_file]

        if question_session_key in st.session_state:
            del st.session_state[question_session_key]

        save_progress()
        st.rerun()


# ============================================================
# 11. ODHLÁSENIE DOLE V SIDEBAR-E
# ============================================================

st.sidebar.divider()
st.sidebar.caption(f"Prihlásený: {st.session_state.display_name}")

if st.sidebar.button("Odhlásiť sa", use_container_width=True):
    logout_user()
