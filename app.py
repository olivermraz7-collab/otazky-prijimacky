import streamlit as st
import json
import random
from streamlit_cookies_manager import EncryptedCookieManager

# --- 1. KONFIGURÁCIA COOKIES ---
# 'prefix' môže byť hocičo, 'password' je potrebný pre šifrovanie (zvoľ si vlastné heslo)
cookies = EncryptedCookieManager(
    prefix="med_prep_v1/",
    password="Heslo1234"
)

if not cookies.ready():
    st.stop()  # Počkáme, kým sa cookies načítajú z prehliadača

# --- 2. ZÁKLADNÉ FUNKCIE ---
def load_questions(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for q in data:
                if 'rep_count' not in q: q['rep_count'] = 0
            return data
    except Exception:
        return []

def save_progress():
    """Uloží celý progres do cookies ako JSON string."""
    cookies['subjects_data'] = json.dumps(st.session_state.subjects_data)
    cookies['last_settings'] = json.dumps({
        "field_idx": st.session_state.selected_field_index,
        "subj_name": st.session_state.selected_subject_name
    })
    cookies.save()

# --- 3. INICIALIZÁCIA DÁT (Z COOKIES) ---
if 'subjects_data' not in st.session_state:
    stored_data = cookies.get('subjects_data')
    st.session_state.subjects_data = json.loads(stored_data) if stored_data else {}

if 'last_settings' not in st.session_state:
    stored_settings = cookies.get('last_settings')
    st.session_state.last_settings = json.loads(stored_settings) if stored_settings else {"field_idx": 0, "subj_name": None}

# --- 4. SIDEBAR A VÝBER ---
st.sidebar.header("Nastavenia")

FIELDS = {
    "Všeobecné lekárstvo": {"Biológia": "biologia.json", "Chémia": "chemia.json"},
    "Urgentná medicína": {"Náuka o spoločnosti": "nos.json", "Fyzika": "fyzika.json", "Biológia": "biologia-urgent.json"}
}

field_list = list(FIELDS.keys())
f_idx = st.session_state.last_settings.get("field_idx", 0)
selected_field_name = st.sidebar.selectbox("Odbor", field_list, index=f_idx if f_idx < len(field_list) else 0)
st.session_state.selected_field_index = field_list.index(selected_field_name)

available_subjects = FIELDS[selected_field_name]
subj_list = list(available_subjects.keys())
default_subj = st.session_state.last_settings.get("subj_name")
s_idx = subj_list.index(default_subj) if default_subj in subj_list else 0

st.session_state.selected_subject_name = st.sidebar.selectbox("Predmet", subj_list, index=s_idx)
selected_file = available_subjects[st.session_state.selected_subject_name]

# Načítanie nového predmetu, ak ešte nie je v pamäti
if selected_file not in st.session_state.subjects_data:
    data = load_questions(selected_file)
    if data:
        random.shuffle(data)
        st.session_state.subjects_data[selected_file] = {"pool": data, "score": 0, "total_count": len(data)}
        save_progress()

current_data = st.session_state.subjects_data[selected_file]

# --- 5. TESTOVACIE ROZHRANIE ---
st.title(f"Príprava: {st.session_state.selected_subject_name}")
pool = current_data["pool"]

if len(pool) > 0:
    q = pool[0]
    if 'answered' not in st.session_state: st.session_state.answered = False

    st.subheader(f"Otázka č. {q['id']}")
    st.write(q['text'])

    user_choices = []
    with st.form(key=f"form_{selected_file}_{q['id']}"):
        for opt in q['options']:
            cb = st.checkbox(opt, key=f"cb_{q['id']}_{opt}", disabled=st.session_state.answered)
            if cb: user_choices.append(opt[0])
        
        btn_label = "Pokračovať" if st.session_state.answered else "Skontrolovať"
        submit = st.form_submit_button(btn_label)

    if submit:
        if not st.session_state.answered:
            st.session_state.answered = True
            st.rerun()
        else:
            # Logika vyhodnotenia
            user_str = "".join(sorted(user_choices))
            correct_str = "".join(sorted(q['answer']))
            
            if user_str == correct_str:
                if q.get('rep_count', 0) == 0:
                    pool.pop(0)
                    current_data["score"] += 1
                elif q.get('rep_count') == 1:
                    q_to_move = pool.pop(0)
                    q_to_move['rep_count'] = 2
                    pool.insert(min(14, len(pool)), q_to_move)
                else:
                    pool.pop(0)
            else:
                wrong_q = pool.pop(0)
                wrong_q['rep_count'] = 1
                pool.insert(min(4, len(pool)), wrong_q)
            
            st.session_state.answered = False
            save_progress()
            st.rerun()

    if st.session_state.answered:
        correct_display = ", ".join(q['answer'])
        if "".join(sorted(user_choices)) == "".join(sorted(q['answer'])):
            st.success(f"Správne! Odpoveď: {correct_display}")
        else:
            st.error(f"Nesprávne! Správna odpoveď: {correct_display}")

    # Štatistiky v sidebare
    st.sidebar.divider()
    st.sidebar.write(f"📊 Body (1. pokus): **{current_data['score']}**")
    st.sidebar.write(f"⏳ Zostáva: **{len(pool)}**")
else:
    st.balloons()
    st.success("Hotovo! Všetky otázky si úspešne zvládol.")
    if st.sidebar.button("Reštartovať tento predmet"):
        del st.session_state.subjects_data[selected_file]
        save_progress()
        st.rerun()
