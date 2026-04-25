import streamlit as st
import json
import random
from streamlit_javascript import st_javascript

# 1. ZÁKLADNÉ NASTAVENIE
st.set_page_config(page_title="Prijímacie skúšky", page_icon="🩺", layout="centered")

# 2. FUNKCIE PRE PRÁCU S PREHLIADAČOM
def set_local_storage(key, value):
    js_code = f"localStorage.setItem('{key}', JSON.stringify({json.dumps(value)}));"
    st_javascript(js_code)

def get_local_storage(key):
    js_code = f"localStorage.getItem('{key}');"
    result = st_javascript(js_code)
    try:
        return json.loads(result) if result else None
    except:
        return None

def load_questions(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for q in data:
                # rep_count: 0 = nová, 1 = po chybe (čaká na 5. miesto), 2 = po 1. oprave (čaká na 15. miesto)
                if 'rep_count' not in q: q['rep_count'] = 0
            return data
    except FileNotFoundError:
        return []

# --- 3. INICIALIZÁCIA A REFRESH POISTKA ---
stored_data = get_local_storage("med_prep_v_final_v2")
stored_settings = get_local_storage("med_settings_v_final_v2")

if stored_data is None and 'init_check' not in st.session_state:
    st.session_state.init_check = True
    st.info("Pripravujem tvoj progres...")
    st.rerun()

if 'subjects_data' not in st.session_state:
    st.session_state.subjects_data = stored_data if stored_data else {}

if 'last_settings' not in st.session_state:
    st.session_state.last_settings = stored_settings if stored_settings else {"field_idx": 0, "subj_name": None}

def sync_all():
    set_local_storage("med_prep_v_final_v2", st.session_state.subjects_data)
    set_local_storage("med_settings_v_final_v2", {
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

        label = "Pokračovať" if st.session_state.answered else "Skontrolovať"
        submit_clicked = st.form_submit_button(label)

    if submit_clicked:
        if not st.session_state.answered:
            st.session_state.answered = True
            st.rerun()
        else:
            user_str = "".join(sorted(user_choices))
            correct_str = "".join(sorted(q['answer']))
            
            if user_str == correct_str:
                if q.get('rep_count', 0) == 0:
                    # Správne na 1. pokus - vymazať z poolu
                    pool.pop(0)
                    current_data["score"] += 1
                elif q.get('rep_count') == 1:
                    # Správne po chybe - posunúť na 15. miesto pre finálne overenie
                    q_to_move = pool.pop(0)
                    q_to_move['rep_count'] = 2
                    pool.insert(min(14, len(pool)), q_to_move)
                else:
                    # Správne v 2. kole opakovania - vymazať definitívne
                    pool.pop(0)
            else:
                # Nesprávne - posunúť na 5. miesto (aktivuje sa 1. kolo opakovania)
                wrong_q = pool.pop(0)
                wrong_q['rep_count'] = 1
                pool.insert(min(4, len(pool)), wrong_q)
            
            st.session_state.answered = False
            sync_all()
            st.rerun()

    if st.session_state.answered:
        correct_display = ", ".join(q['answer'])
        user_str = "".join(sorted(user_choices))
        if user_str == "".join(sorted(q['answer'])):
            st.success(f"Správne! Odpoveď: {correct_display}")
        else:
            st.error(f"Nesprávne! Správna odpoveď: {correct_display}")

    st.sidebar.divider()
    st.sidebar.write(f"📊 Body (na 1. pokus): **{current_data['score']}**")
    st.sidebar.write(f"⏳ Zostáva v obehu: **{len(pool)}**")

else:
    st.balloons()
    st.success("Všetko hotové! Si pripravený na skúšky.")
    if st.sidebar.button("Reštartovať predmet"):
        del st.session_state.subjects_data[selected_file]
        sync_all()
        st.rerun()
