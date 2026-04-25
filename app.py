import streamlit as st
import json
import random
import time
from streamlit_javascript import st_javascript

# 1. ZÁKLADNÉ NASTAVENIE
st.set_page_config(page_title="Prijímacie skúšky", page_icon="🩺", layout="centered")

# Kľúč pre LocalStorage - zmeň ho na úplne nový (v3), aby sme začali načisto
DB_KEY = "med_final_v3"
SETTINGS_KEY = "med_settings_v3"

# 2. FUNKCIE PRE PRÁCU S PREHLIADAČOM
def set_local_storage(key, value):
    # Uložíme len ak máme čo ukladať a ak už prebehlo úvodné načítanie
    if value:
        js_code = f"localStorage.setItem('{key}', JSON.stringify({json.dumps(value)}));"
        st_javascript(js_code)

def get_local_storage(key):
    js_code = f"localStorage.getItem('{key}');"
    result = st_javascript(js_code)
    if result:
        try:
            return json.loads(result)
        except:
            return None
    return None

def load_questions(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for q in data:
                if 'rep_count' not in q: q['rep_count'] = 0
            return data
    except FileNotFoundError:
        return []

# --- 3. MOZOG APLIKÁCIE: NAČÍTANIE A POISTKA ---

# Skúsime získať dáta
raw_data = get_local_storage(DB_KEY)
raw_settings = get_local_storage(SETTINGS_KEY)

# Ak je v session_state 'data_loaded', vieme, že sme už úspešne naštartovali
if "data_loaded" not in st.session_state:
    if raw_data is None:
        # Ak JS ešte nič nevrátil, vypíšeme info a čakáme
        st.info("Pripravujem tvoj progres... Prosím chvíľu počkaj.")
        # Ak po 2 sekundách nič nepríde, možno je to nový používateľ
        time.sleep(0.5) 
        if raw_data is not None or raw_settings is not None:
             st.session_state.data_loaded = True
             st.rerun()
        # Ak používateľ klikne na "Začať ako nový", uvoľníme to
        if st.button("Ak načítavanie trvá dlho, klikni sem"):
            st.session_state.data_loaded = True
            st.rerun()
        st.stop() # Tu sa kód zastaví, kým JS nevráti výsledok
    else:
        st.session_state.data_loaded = True

# Inicializácia session_state až po potvrdení načítania
if 'subjects_data' not in st.session_state:
    st.session_state.subjects_data = raw_data if raw_data else {}

if 'last_settings' not in st.session_state:
    st.session_state.last_settings = raw_settings if raw_settings else {"field_idx": 0, "subj_name": None}

def sync_all():
    """Uloží všetko, ale len ak sú dáta pripravené."""
    if st.session_state.get("data_loaded"):
        set_local_storage(DB_KEY, st.session_state.subjects_data)
        set_local_storage(SETTINGS_KEY, {
            "field_idx": st.session_state.selected_field_index,
            "subj_name": st.session_state.selected_subject_name
        })

# --- 4. SIDEBAR ---
FIELDS = {
    "Všeobecné lekárstvo": {"Biológia": "biologia.json", "Chémia": "chemia.json"},
    "Urgentná medicína": {"Náuka o spoločnosti": "nos.json", "Fyzika": "fyzika.json", "Biológia": "biologia-urgent.json"}
}

field_list = list(FIELDS.keys())
selected_field_name = st.sidebar.selectbox("Odbor", field_list, index=st.session_state.last_settings.get("field_idx", 0))
st.session_state.selected_field_index = field_list.index(selected_field_name)

available_subjects = FIELDS[selected_field_name]
subj_list = list(available_subjects.keys())
default_subj = st.session_state.last_settings.get("subj_name")
if default_subj not in subj_list: default_subj = subj_list[0]

st.session_state.selected_subject_name = st.sidebar.selectbox("Predmet", subj_list, index=subj_list.index(default_subj))
selected_file = available_subjects[st.session_state.selected_subject_name]

# Inicializácia predmetu (iba ak neexistuje v načítaných dátach)
if selected_file not in st.session_state.subjects_data:
    data = load_questions(selected_file)
    if data:
        random.shuffle(data)
        st.session_state.subjects_data[selected_file] = {"pool": data, "score": 0, "total_count": len(data)}
        sync_all()

current_data = st.session_state.subjects_data[selected_file]

# --- 5. HLAVNÁ ČASŤ (TEST) ---
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
            cb = st.checkbox(opt, key=f"cb_{selected_file}_{q['id']}_{opt}", disabled=st.session_state.answered)
            if cb: user_choices.append(opt[0])
        submit_clicked = st.form_submit_button("Pokračovať" if st.session_state.answered else "Skontrolovať")

    if submit_clicked:
        if not st.session_state.answered:
            st.session_state.answered = True
            st.rerun()
        else:
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
            sync_all()
            st.rerun()

    if st.session_state.answered:
        correct_display = ", ".join(q['answer'])
        if "".join(sorted(user_choices)) == "".join(sorted(q['answer'])):
            st.success(f"Správne! Odpoveď: {correct_display}")
        else:
            st.error(f"Nesprávne! Správna odpoveď: {correct_display}")

    st.sidebar.divider()
    st.sidebar.write(f"📊 Body (1. pokus): **{current_data['score']}**")
    st.sidebar.write(f"⏳ Zostáva v obehu: **{len(pool)}**")
else:
    st.balloons()
    st.success("Všetko hotové!")
    if st.sidebar.button("Reštartovať predmet"):
        del st.session_state.subjects_data[selected_file]
        sync_all()
        st.rerun()
