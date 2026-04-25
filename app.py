import streamlit as st
import json
import random
import os

st.set_page_config(page_title="Prijímacie skúšky", page_icon="🩺", layout="centered")

# --- KONŠTANTY ---
SAVE_FILE = "progress_save.json"

def load_questions(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for q in data:
                if 'repetition_mode' not in q:
                    q['repetition_mode'] = False
            return data
    except FileNotFoundError:
        return []

def save_all_progress():
    """Uloží kompletný stav zo session_state do súboru."""
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.subjects_data, f, ensure_ascii=False, indent=4)

def load_all_progress():
    """Načíta uložený progres zo súboru, ak existuje."""
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

# --- DEFINÍCIA ODBOROV ---
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

# --- INICIALIZÁCIA ---
if 'subjects_data' not in st.session_state:
    # Skúsime načítať dáta z disku, inak prázdny slovník
    st.session_state.subjects_data = load_all_progress()

if 'selected_field_index' not in st.session_state:
    st.session_state.selected_field_index = 0

if 'selected_subject_name' not in st.session_state:
    st.session_state.selected_subject_name = None

# --- SIDEBAR ---
st.sidebar.header("Nastavenia štúdia")

selected_field_name = st.sidebar.selectbox(
    "Vyber si odbor", 
    list(FIELDS.keys()), 
    index=st.session_state.selected_field_index, 
    key="field_selector"
)
st.session_state.selected_field_index = list(FIELDS.keys()).index(selected_field_name)

available_subjects = FIELDS[selected_field_name]
if st.session_state.selected_subject_name not in available_subjects:
    st.session_state.selected_subject_name = list(available_subjects.keys())[0]

subject_display_name = st.sidebar.selectbox(
    "Vyber si predmet", 
    list(available_subjects.keys()), 
    index=list(available_subjects.keys()).index(st.session_state.selected_subject_name),
    key="subject_selector"
)
st.session_state.selected_subject_name = subject_display_name
selected_file = available_subjects[subject_display_name]

# Načítanie otázok ak ešte nie sú v pamäti (ani v uloženej)
if selected_file not in st.session_state.subjects_data:
    data = load_questions(selected_file)
    if data:
        random.shuffle(data)
        st.session_state.subjects_data[selected_file] = {
            "pool": data,
            "score": 0,
            "total_count": len(data)
        }
    else:
        st.session_state.subjects_data[selected_file] = {"pool": [], "score": 0, "total_count": 0}

current_data = st.session_state.subjects_data[selected_file]

# Reset tlačidlo
if st.sidebar.button("Reštartovať aktuálny predmet"):
    if selected_file in st.session_state.subjects_data:
        del st.session_state.subjects_data[selected_file]
        save_all_progress() # Uložiť zmenu (vymazanie)
        st.rerun()

# --- HLAVNÁ ČASŤ ---
if selected_field_name == "Všeobecné lekárstvo":
    st.title("🩺 Príprava na LF")
else:
    st.title("🚑 Urgentná medicína")

pool = current_data["pool"]

if len(pool) > 0:
    q = pool[0]
    if q.get('repetition_mode'):
        st.info("🔄 OPAKOVANIE CHYBY")

    st.subheader(f"Otázka č. {q['id']}")
    st.write(q['text'])

    user_choices = []
    with st.form(key=f"form_{selected_file}_{q['id']}"):
        for opt in q['options']:
            if st.checkbox(opt, key=f"cb_{selected_file}_{q['id']}_{opt}"):
                user_choices.append(opt[0])
        submit_button = st.form_submit_button(label='Overiť odpoveď')

    if submit_button:
        user_str = "".join(sorted(user_choices))
        correct_str = "".join(sorted(q['answer']))

        if user_str == correct_str:
            st.success(f"✅ SPRÁVNE! ({q['answer']})")
            if q.get('repetition_mode'):
                q_to_move = pool.pop(0)
                new_index = min(9, len(pool)) 
                pool.insert(new_index, q_to_move)
            else:
                pool.pop(0)
                current_data["score"] += 1
        else:
            st.error(f"❌ NESPRÁVNE! Správne: {q['answer']}")
            wrong_q = pool.pop(0)
            wrong_q['repetition_mode'] = True
            new_index = min(4, len(pool))
            pool.insert(new_index, wrong_q)

        # KLÚČOVÝ KROK: Uložíme progres hneď po odpovedi
        save_all_progress()
        
        if st.button("Pokračovať"):
            st.rerun()
    
    # Štatistiky v sidebar
    st.sidebar.divider()
    st.sidebar.write(f"📊 Správne (1. pokus): **{current_data['score']}**")
    st.sidebar.write(f"⏳ Zostáva: **{len(pool)}** / {current_data['total_count']}")
    
else:
    if current_data["total_count"] > 0:
        st.balloons()
        st.success("Všetko hotové!")
    else:
        st.warning("Žiadne otázky v súbore.")
