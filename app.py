import streamlit as st
import json
import re
import random
import os
import hashlib
import secrets
from streamlit_cookies_manager import EncryptedCookieManager

st.set_page_config(
    page_title="Medicína Príprava",
    layout="centered"
)

# ============================================================
# 1. COOKIES - MINIMÁLNE POUŽITIE
#    Cookies sa používajú IBA na zapamätanie prihláseného používateľa.
#    Progres otázok sa do cookies NEUKLADÁ.
# ============================================================

cookies = EncryptedCookieManager(
    prefix="med_prep_v3/",
    password="Heslo1234"
)

if not cookies.ready():
    st.stop()


# ============================================================
# 2. CESTY A SÚBORY
# ============================================================

DATA_DIR = "data"
PROGRESS_DIR = os.path.join(DATA_DIR, "progress")
USERS_FILE = os.path.join(DATA_DIR, "users.json")


def ensure_data_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PROGRESS_DIR, exist_ok=True)


ensure_data_dirs()


# ============================================================
# 3. JSON FUNKCIE
# ============================================================

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
    """
    Cookie obsahuje iba username.
    Žiadny progres otázok sa sem neukladá.
    """
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

    # Do cookies ide iba krátke username.
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


# Automatické prihlásenie z cookie
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
#    Progres sa ukladá iba do data/progress/{username}.json
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
    """
    Dôležité:
    Progres sa NEUKLADÁ do cookies.
    Ukladá sa iba do JSON súboru používateľa.
    """
    username = st.session_state.username

    user_state = {
        "subjects_data": st.session_state.subjects_data,
        "last_settings": {
            "field_idx": st.session_state.selected_field_index,
            "subj_name": st.session_state.selected_subject_name
        }
    }

    save_user_state(username, user_state)


# Načítanie progresu konkrétneho používateľa
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
# 6. ZÁKLADNÉ FUNKCIE OTÁZOK
# ============================================================

def load_questions(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

            for q in data:
                if "rep_count" not in q:
                    q["rep_count"] = 0

            return data

    except Exception:
        return []


# ============================================================
# 7. SIDEBAR A VÝBER PREDMETU
# ============================================================

st.sidebar.header("Nastavenia")

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

if selected_file not in st.session_state.subjects_data:
    data = load_questions(selected_file)

    if data:
        random.shuffle(data)

        st.session_state.subjects_data[selected_file] = {
            "pool": data,
            "score": 0,
            "total_count": len(data)
        }

        save_progress()
    else:
        st.title(f"Príprava: {st.session_state.selected_subject_name}")
        st.error(f"Nepodarilo sa načítať súbor: {selected_file}")

        st.sidebar.divider()
        st.sidebar.caption(f"Prihlásený: {st.session_state.display_name}")

        if st.sidebar.button("Odhlásiť sa", use_container_width=True):
            logout_user()

        st.stop()

current_data = st.session_state.subjects_data[selected_file]
pool = current_data["pool"]


# ============================================================
# 8. TESTOVACIE ROZHRANIE
# ============================================================

st.title(f"Príprava: {st.session_state.selected_subject_name}")

if len(pool) > 0:
    q = pool[0]

    if "answered" not in st.session_state:
        st.session_state.answered = False

    st.subheader(f"Otázka č. {q['id']}")

    # Zobrazenie textu otázky s podporou obrázkov
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

    # FORMULÁR S MOŽNOSŤAMI
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
                    key=f"cb_{q['id']}_{opt}",
                    disabled=st.session_state.answered
                )

                try:
                    st.image(f"images/{img_filename}", width=250)
                except Exception:
                    st.warning(f"Súbor {img_filename} chýba.")
            else:
                cb = st.checkbox(
                    opt,
                    key=f"cb_{q['id']}_{opt}",
                    disabled=st.session_state.answered
                )

            if cb:
                user_choices.append(opt[0])

        btn_label = "Pokračovať" if st.session_state.answered else "Skontrolovať"
        submit = st.form_submit_button(btn_label)

    # Vyhodnotenie
    if submit:
        if not st.session_state.answered:
            st.session_state.answered = True
            st.rerun()
        else:
            user_str = "".join(sorted(user_choices))
            correct_str = "".join(sorted(q["answer"]))

            if user_str == correct_str:
                if q.get("rep_count", 0) == 0:
                    pool.pop(0)
                    current_data["score"] += 1

                elif q.get("rep_count") == 1:
                    q_to_move = pool.pop(0)
                    q_to_move["rep_count"] = 2
                    pool.insert(min(14, len(pool)), q_to_move)

                else:
                    pool.pop(0)

            else:
                wrong_q = pool.pop(0)
                wrong_q["rep_count"] = 1
                pool.insert(min(4, len(pool)), wrong_q)

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

    # Tlačidlo na nahlásenie chyby je pod otázkou
    form_url = (
        f"https://docs.google.com/forms/d/e/1FAIpQLScVa1VK6mJYX6YRmgcms64AMxaTm5wSDmJF9vnl1M4QzzmCUw/viewform"
        f"?usp=pp_url"
        f"&entry.424182118={q['id']}"
        f"&entry.1513577736={st.session_state.selected_subject_name}"
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

    # ========================================================
    # 9. SIDEBAR ŠTATISTIKY
    # ========================================================

    st.sidebar.divider()
    st.sidebar.write(f"📊 Body: **{current_data['score']}**")
    st.sidebar.write(f"⏳ Zostáva: **{len(pool)}**")

else:
    st.balloons()
    st.success("Hotovo!")

    if st.sidebar.button("Reštartovať predmet"):
        del st.session_state.subjects_data[selected_file]
        save_progress()
        st.rerun()


# ============================================================
# 10. ODHLÁSENIE DOLE V SIDEBAR-E
# ============================================================

st.sidebar.divider()
st.sidebar.caption(f"Prihlásený: {st.session_state.display_name}")

if st.sidebar.button("Odhlásiť sa", use_container_width=True):
    logout_user()
