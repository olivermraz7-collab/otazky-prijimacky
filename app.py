import streamlit as st
import json
import random
import os

st.set_page_config(page_title="LF Test", page_icon="🩺", layout="centered")

def load_questions(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for q in data:
                if 'repetition_mode' not in q:
                    q['repetition_mode'] = False
            return data
    except FileNotFoundError:
        st.error(f"Súbor {file_path} nebol nájdený.")
        return []

st.title("🩺 Príprava na prijímačky LF")

# --- DEFINÍCIA ODBOROV A PREDMETOV ---
# Kľúč: Názov predmetu, Hodnota: názov .json súboru
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

# --- SIDEBAR VÝBER ---
st.sidebar.header("Nastavenia štúdia")
selected_field = st.sidebar.selectbox("Vyber si odbor", list(FIELDS.keys()))

# Dynamický výber predmetu na základe odboru
available_subjects = FIELDS[selected_field]
subject_display_name = st.sidebar.selectbox("Vyber si predmet", list(available_subjects.keys()))
selected_file = available_subjects[subject_display_name]

# --- LOGIKA RELÁCIE ---
if 'current_file' not in st.session_state or st.session_state.current_file != selected_file:
    data = load_questions(selected_file)
    if data:
        st.session_state.pool = data
        random.shuffle(st.session_state.pool)
        st.session_state.score = 0
        st.session_state.total_count = len(st.session_state.pool)
        st.session_state.current_file = selected_file
    else:
        st.session_state.pool = []

if st.sidebar.button("Reštartovať predmet"):
    st.session_state.current_file = None
    st.rerun()

# --- HLAVNÝ TEST ---
if len(st.session_state.pool) > 0:
    q = st.session_state.pool[0]
    
    if q.get('repetition_mode'):
        st.info("🔄 OPAKOVANIE CHYBY")

    st.subheader(f"Otázka č. {q['id']}")
    st.write(q['text'])

    user_choices = []
    with st.form(key=f"form_{selected_file}_{q['id']}"):
        for opt in q['options']:
            if st.checkbox(opt, key=f"cb_{q['id']}_{opt}"):
                user_choices.append(opt[0])

        submit_button = st.form_submit_button(label='Overiť odpoveď')

    if submit_button:
        user_str = "".join(sorted(user_choices))
        correct_str = "".join(sorted(q['answer']))

        if user_str == correct_str:
            st.success(f"✅ SPRÁVNE! (Odpoveď: {q['answer']})")
            
            if q.get('repetition_mode'):
                # Ak bola predtým chyba, posuň o 10 miest (alebo na koniec)
                q_to_move = st.session_state.pool.pop(0)
                new_index = min(9, len(st.session_state.pool))
                st.session_state.pool.insert(new_index, q_to_move)
                st.info(f"Uložené do pamäte. Zopakujeme si ju o {new_index} otázok.")
            else:
                # Správne na prvýkrát - vymazať
                st.session_state.pool.pop(0)
                st.session_state.score += 1
        else:
            st.error(f"❌ NESPRÁVNE! Správna odpoveď bola: {q['answer']}")
            
            # Chyba - posuň o 5 miest a zapni repetition_mode
            wrong_q = st.session_state.pool.pop(0)
            wrong_q['repetition_mode'] = True
            
            new_index = min(4, len(st.session_state.pool))
            st.session_state.pool.insert(new_index, wrong_q)
            st.warning(f"Presunuté o {new_index} miest ďalej.")

        if st.button("Pokračovať"):
            st.rerun()
    
    st.sidebar.divider()
    st.sidebar.write(f"🎓 Odbor: **{selected_field}**")
    st.sidebar.write(f"📊 Vyradené otázky: **{st.session_state.score}** / {st.session_state.total_count}")
    st.sidebar.write(f"📝 Otázok v obehu: {len(st.session_state.pool)}")
    
else:
    if 'current_file' in st.session_state:
        st.balloons()
        st.success(f"Gratulujem! Ovládaš všetky otázky z predmetu {subject_display_name}!")
