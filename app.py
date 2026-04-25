import streamlit as st
import json
import random
from streamlit_javascript import st_javascript

# 1. ZÁKLADNÉ NASTAVENIE
st.set_page_config(page_title="Prijímacie skúšky", page_icon="🩺", layout="centered")

# Kľúče (v4 pre čistý štart)
DB_KEY = "med_final_v4"
SETTINGS_KEY = "med_settings_v4"

# 2. FUNKCIE
def set_local_storage(key, value):
    if value:
        js_code = f"localStorage.setItem('{key}', JSON.stringify({json.dumps(value)}));"
        st_javascript(js_code)

def get_local_storage(key):
    js_code = f"localStorage.getItem('{key}');"
    return st_javascript(js_code)

def load_questions(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for q in data:
                if 'rep_count' not in q: q['rep_count'] = 0
            return data
    except Exception:
        return []

# --- 3. LOGIKA NAČÍTANIA ---
# Skúsime načítať dáta z JS
js_data = get_local_storage(DB_KEY)
js_settings = get_local_storage(SETTINGS_KEY)

# Ak už máme dáta v session_state, nič neriešime. 
# Ak nie, skúsime ich tam dostať z JS.
if "subjects_data" not in st.session_state:
    if js_data is not None:
        try:
            # Ak JS vrátil text, skúsime ho dekódovať
            st.session_state.subjects_data = json.loads(js_data)
        except:
            st.session_state.subjects_data = {}
    else:
        # Ak JS ešte nič nevrátil, zatiaľ neinicializujeme (aby sme neprepísali nulu)
        st.info("Pripravujem tvoj progres... Ak toto trvá viac ako 3 sekundy, začni vybratím predmetu vľavo.")
        # Ak chceme povoliť okamžitý štart, ak je to nový používateľ:
        if st.button("Začať nanovo / Preskočiť načítavanie"):
            st.session_state.subjects_data = {}
            st.rerun()
        st.stop()

if "last_settings" not in st.session_state:
    if js_settings is not None:
        try:
            st.session_state.last_settings = json.loads(js_settings)
        except:
            st.session_state.last_settings = {"field_idx": 0, "subj_name": None}
    else:
        st.session_state.last_settings = {"field_idx": 0, "subj_name": None}

def sync_all():
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
f_idx = st.session_state.last_settings.get("field_idx", 0)
selected_field_name = st.sidebar.selectbox("Odbor", field_list, index=f_idx if f_idx < len(field_list) else 0)
st.session_state.selected_field_index = field_list.index(selected_field_name)

available_subjects = FIELDS[selected_field_name]
subj_list = list(available_subjects.keys())
default_subj = st.session_state.last_settings.get("subj_name")
s_idx = subj_list.index(default_subj) if default_subj in subj_list else 0

st.session_state.selected_subject_name = st.sidebar.selectbox("Predmet", subj_list, index=s_idx)
selected_file = available_subjects[st.session_state.selected_subject_name]

# Inicializácia poolu
if selected_file not in st.session_state.subjects_data:
    data = load_questions(selected_file)
    if data:
        random.shuffle(data)
        st.session_state.subjects_data[selected_file] = {"pool": data, "score": 0, "total_count": len(data)}
        sync_all()

current_data = st.session_state.subjects_data[selected_file]

# --- 5. TEST ---
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
            user_choices_str = "".join(sorted(user_choices))
            correct_str = "".join(sorted(q['answer']))
            
            if user_choices_str == correct_str:
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
    st.sidebar.write(f"⏳ Zostáva: **{len(pool)}**")
else:
    st.balloons()
    st.success("Hotovo!")
    if st.sidebar.button("Reštartovať predmet"):
        del st.session_state.subjects_data[selected_file]
        sync_all()
        st.rerun()
