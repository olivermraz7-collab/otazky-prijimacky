import streamlit as st
import json
import random
from streamlit_javascript import st_javascript

# --- KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="Prijímacie skúšky", page_icon="🩺", layout="centered")

# --- POMOCNÉ FUNKCIE PRE LOCALSTORAGE (TRVALÝ PROGRES) ---
def set_local_storage(key, value):
    """Uloží dáta priamo do prehliadača používateľa."""
    js_code = f"localStorage.setItem('{key}', JSON.stringify({json.dumps(value)}));"
    st_javascript(js_code)

def get_local_storage(key):
    """Načíta dáta z prehliadača používateľa."""
    js_code = f"localStorage.getItem('{key}');"
    result = st_javascript(js_code)
    try:
        return json.loads(result) if result else None
    except:
        return None

# --- NAČÍTANIE OTÁZOK ZO SÚBOROV ---
def load_questions(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for q in data:
                if 'repetition_mode' not in q: q['repetition_mode'] = False
            return data
    except FileNotFoundError:
        return []

# --- DEFINÍCIA ODBOROV A PREDMETOV ---
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

# --- INICIALIZÁCIA PAMÄTE (AUTO-LOAD) ---
# Načítame progres z prehliadača hneď po zapnutí
if 'subjects_data' not in st.session_state:
    stored_data = get_local_storage("med_prep_data_v2")
    st.session_state.subjects_data = stored_data if stored_data else {}

if 'last_settings' not in st.session_state:
    stored_settings = get_local_storage("med_settings_v2")
    st.session_state.last_settings = stored_settings if stored_settings else {"field_idx": 0, "subj_name": None}

def sync_all():
    """Automaticky uloží všetko do prehliadača."""
    set_local_storage("med_prep_data_v2", st.session_state.subjects_data)
    set_local_storage("med_settings_v2", {
        "field_idx": st.session_state.selected_field_index,
        "subj_name": st.session_state.selected_subject_name
    })

# --- SIDEBAR NASTAVENIA ---
st.sidebar.header("Nastavenia štúdia")

field_list = list(FIELDS.keys())
selected_field_name = st.sidebar.selectbox(
    "Vyber si odbor", 
    field_list, 
    index=st.session_state.last_settings.get("field_idx", 0)
)
st.session_state.selected_field_index = field_list.index(selected_field_name)

available_subjects = FIELDS[selected_field_name]
subj_list = list(available_subjects.keys())

default_subj = st.session_state.last_settings.get("subj_name")
if default_subj not in subj_list:
    default_subj = subj_list[0]

st.session_state.selected_subject_name = st.sidebar.selectbox(
    "Vyber si predmet", 
    subj_list, 
    index=subj_list.index(default_subj)
)

selected_file = available_subjects[st.session_state.selected_subject_name]

# Inicializácia otázok pre konkrétny súbor, ak ešte nie sú v pamäti
if selected_file not in st.session_state.subjects_data:
    data = load_questions(selected_file)
    if data:
        random.shuffle(data)
        st.session_state.subjects_data[selected_file] = {
            "pool": data, 
            "score": 0, 
            "total_count": len(data)
        }
        sync_all()
    else:
        st.session_state.subjects_data[selected_file] = {"pool": [], "score": 0, "total_count": 0}

current_data = st.session_state.subjects_data[selected_file]

# Reset tlačidlo v sidebare
if st.sidebar.button("Reštartovať tento predmet"):
    del st.session_state.subjects_data[selected_file]
    sync_all()
    st.rerun()

# --- HLAVNÁ ČASŤ TESTU ---
st.title(f"Príprava: {st.session_state.selected_subject_name}")
pool = current_data["pool"]

if len(pool) > 0:
    q = pool[0]
    
    # Príznak, či sme už v stave "skontrolované"
    if 'answered' not in st.session_state:
        st.session_state.answered = False

    st.subheader(f"Otázka č. {q['id']}")
    st.write(q['text'])

    # 1. FORMULÁR S ODPOVEĎAMI
    with st.form(key=f"form_{selected_file}_{q['id']}"):
        user_choices = []
        for opt in q['options']:
            # Ak je už skontrolované, checkboxy sú zamknuté (disabled)
            cb = st.checkbox(opt, key=f"cb_{selected_file}_{q['id']}_{opt}", disabled=st.session_state.answered)
            if cb:
                user_choices.append(opt[0])
        
        # DYNAMICKÉ TLAČIDLO (Menia sa nápis aj funkcia)
        label = "Pokračovať ➡️" if st.session_state.answered else "Skontrolovať 🔍"
        submit_clicked = st.form_submit_button(label)

    # 2. LOGIKA TLAČIDLA
    if submit_clicked:
        if not st.session_state.answered:
            # FÁZA 1: Používateľ klikol na Skontrolovať
            st.session_state.answered = True
            st.rerun() # Refresh pre zmenu tlačidla a zamknutie checkboxov
        else:
            # FÁZA 2: Používateľ klikol na Pokračovať
            user_str = "".join(sorted(user_choices))
            correct_str = "".join(sorted(q['answer']))

            if user_str == correct_str:
                if q.get('repetition_mode'):
                    q_to_move = pool.pop(0)
                    pool.insert(min(9, len(pool)), q_to_move)
                else:
                    pool.pop(0)
                    current_data["score"] += 1
            else:
                wrong_q = pool.pop(0)
                wrong_q['repetition_mode'] = True
                pool.insert(min(4, len(pool)), wrong_q)
            
            # Resetujeme stav pre novú otázku
            st.session_state.answered = False
            sync_all() # Uložíme zmeny do prehliadača
            st.rerun()

    # 3. ZOBRAZENIE SPÄTNEJ VÄZBY (po kliknutí na Skontrolovať)
    if st.session_state.answered:
        user_str = "".join(sorted(user_choices))
        correct_str = "".join(sorted(q['answer']))
        
        if user_str == correct_str:
            st.success(f"✅ SPRÁVNE! Odpoveď: **{q['answer']}**")
        else:
            st.error(f"❌ NESPRÁVNE! Správna odpoveď: **{q['answer']}**")
            st.info(f"Tvoja odpoveď: {user_str if user_str else 'žiadna'}")

    # ŠTATISTIKY V SIDEBARE
    st.sidebar.divider()
    st.sidebar.write(f"🎓 Odbor: **{selected_field_name}**")
    st.sidebar.write(f"📊 Správne (1. pokus): **{current_data['score']}**")
    st.sidebar.write(f"⏳ Zostáva: **{len(pool)}** / {current_data['total_count']}")

else:
    # AK SÚ VŠETKY OTÁZKY HOTOVÉ
    st.balloons()
    st.success(f"Gratulujem! Prešiel si všetky otázky z predmetu {st.session_state.selected_subject_name}!")
    if st.button("Začať tento predmet odznova"):
        del st.session_state.subjects_data[selected_file]
        sync_all()
        st.rerun()
    
