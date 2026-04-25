import streamlit as st
import json
import random
import extra_streamlit_components as stx

st.set_page_config(page_title="Prijímacie skúšky", page_icon="🩺", layout="centered")

# --- INICIALIZÁCIA COOKIE MANAGERA ---
@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

def load_questions(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for q in data:
                if 'repetition_mode' not in q: q['repetition_mode'] = False
            return data
    except FileNotFoundError:
        return []

# --- DEFINÍCIA ODBOROV ---
FIELDS = {
    "Všeobecné lekárstvo": {
        "Biológia": "biologia.json",
        "Chémia": "chemia.json"
    },
    "Urgentná medicína": {
        "Náuka o spoločnosti": "nos.json",
        "Fyzika": "fyzika.json",
        "Biológia (Urgent)": "biologia-urgent.json"
    }
}

# --- NAČÍTANIE PROGRESU Z COOKIES ---
# Cookies sa načítavajú asynchrónne, preto musíme chvíľu počkať alebo overiť ich existenciu
saved_progress = cookie_manager.get("med_progress")
saved_settings = cookie_manager.get("med_settings")

if 'subjects_data' not in st.session_state:
    if saved_progress:
        st.session_state.subjects_data = json.loads(saved_progress)
    else:
        st.session_state.subjects_data = {}

if 'last_settings' not in st.session_state:
    if saved_settings:
        st.session_state.last_settings = json.loads(saved_settings)
    else:
        st.session_state.last_settings = {"field_idx": 0, "subj_name": None}

def auto_save():
    """Uloží aktuálny stav do cookies s platnosťou na 30 dní."""
    cookie_manager.set("med_progress", json.dumps(st.session_state.subjects_data), max_age=2592000)
    cookie_manager.set("med_settings", json.dumps({
        "field_idx": st.session_state.selected_field_index,
        "subj_name": st.session_state.selected_subject_name
    }), max_age=2592000)

# --- SIDEBAR ---
st.sidebar.header("Nastavenia štúdia")

# Výber odboru (berie z uložených nastavení)
field_list = list(FIELDS.keys())
selected_field_name = st.sidebar.selectbox(
    "Vyber si odbor", 
    field_list, 
    index=st.session_state.last_settings["field_idx"]
)
st.session_state.selected_field_index = field_list.index(selected_field_name)

available_subjects = FIELDS[selected_field_name]
subj_list = list(available_subjects.keys())

# Výber predmetu (berie z uložených nastavení)
default_subj = st.session_state.last_settings["subj_name"]
if default_subj not in subj_list:
    default_subj = subj_list[0]

st.session_state.selected_subject_name = st.sidebar.selectbox(
    "Vyber si predmet", 
    subj_list, 
    index=subj_list.index(default_subj)
)

selected_file = available_subjects[st.session_state.selected_subject_name]

# Inicializácia otázok
if selected_file not in st.session_state.subjects_data:
    data = load_questions(selected_file)
    if data:
        random.shuffle(data)
        st.session_state.subjects_data[selected_file] = {"pool": data, "score": 0, "total_count": len(data)}
        auto_save()
    else:
        st.session_state.subjects_data[selected_file] = {"pool": [], "score": 0, "total_count": 0}

current_data = st.session_state.subjects_data[selected_file]

# Reset tlačidlo
if st.sidebar.button("Reštartovať predmet"):
    del st.session_state.subjects_data[selected_file]
    auto_save()
    st.rerun()

# --- HLAVNÝ TEST ---
st.title(f"Príprava: {st.session_state.selected_subject_name}")
pool = current_data["pool"]

if len(pool) > 0:
    q = pool[0]
    st.subheader(f"Otázka č. {q['id']}")
    st.write(q['text'])

    with st.form(key=f"form_{selected_file}_{q['id']}"):
        user_choices = []
        for opt in q['options']:
            if st.checkbox(opt, key=f"cb_{selected_file}_{q['id']}_{opt}"):
                user_choices.append(opt[0])
        
        if st.form_submit_button("Overiť"):
            user_str = "".join(sorted(user_choices))
            correct_str = "".join(sorted(q['answer']))

            if user_str == correct_str:
                st.success("Správne!")
                if q.get('repetition_mode'):
                    q_to_move = pool.pop(0)
                    pool.insert(min(9, len(pool)), q_to_move)
                else:
                    pool.pop(0)
                    current_data["score"] += 1
            else:
                st.error(f"Nesprávne! Správne: {q['answer']}")
                wrong_q = pool.pop(0)
                wrong_q['repetition_mode'] = True
                pool.insert(min(4, len(pool)), wrong_q)

            auto_save() # Automatické uloženie progresu
            st.button("Pokračovať")

    st.sidebar.divider()
    st.sidebar.write(f"📊 Správne: **{current_data['score']}**")
    st.sidebar.write(f"⏳ Zostáva: **{len(pool)}** / {current_data['total_count']}")
else:
    st.success("Hotovo! Všetky otázky z tohto predmetu si prešiel.")
