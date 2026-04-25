import streamlit as st
import json
import random
import os

st.set_page_config(page_title="LF Test", page_icon="🩺", layout="centered")

# Funkcia na načítanie otázok zo súborov
def load_questions(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

st.title("🩺 Príprava na prijímačky LF")

# Automaticky nájde dostupné predmety (json súbory)
available_files = [f for f in os.listdir('.') if f.endswith('.json')]
subject_map = {f.replace('.json', '').capitalize(): f for f in available_files}

if not subject_map:
    st.error("Chýbajú dátové súbory (.json). Nahraj biologia.json a chemia.json na GitHub.")
else:
    subject_name = st.sidebar.selectbox("Vyber si predmet", list(subject_map.keys()))
    selected_file = subject_map[subject_name]

    # Inicializácia relácie
    if 'current_file' not in st.session_state or st.session_state.current_file != selected_file:
        data = load_questions(selected_file)
        st.session_state.pool = data
        random.shuffle(st.session_state.pool)
        st.session_state.score = 0
        st.session_state.total = len(data)
        st.session_state.current_file = selected_file
        st.session_state.wrong_ones = []

    if st.sidebar.button("Reštartovať tento predmet"):
        st.session_state.current_file = None
        st.rerun()

    if len(st.session_state.pool) > 0:
        q = st.session_state.pool[0]
        
        st.progress(1.0 - (len(st.session_state.pool) / st.session_state.total))
        st.subheader(f"Otázka č. {q['id']}")
        st.write(q['text'])

        # Generovanie checkboxov pre možnosti
        user_choices = []
        for opt in q['options']:
            if st.checkbox(opt, key=f"{q['id']}_{opt}"):
                user_choices.append(opt[0]) # Získa písmeno A, B, C...

        if st.button("Overiť odpoveď"):
            user_str = "".join(sorted(user_choices))
            correct_str = "".join(sorted(q['answer']))

            if user_str == correct_str:
                st.success(f"✅ SPRÁVNE! (Odpoveď: {q['answer']})")
                st.session_state.score += 1
                st.session_state.pool.pop(0)
                if st.button("Ďalšia otázka"):
                    st.rerun()
            else:
                st.error(f"❌ NESPRÁVNE! Správna odpoveď bola: {q['answer']}")
                # Presun na koniec, aby sa opakovala
                wrong_q = st.session_state.pool.pop(0)
                st.session_state.pool.append(wrong_q)
                if st.button("Skúsiť inú"):
                    st.rerun()
        
        st.sidebar.write(f"Skóre: {st.session_state.score} / {st.session_state.total}")
        st.sidebar.write(f"Zostáva v balíku: {len(st.session_state.pool)}")
    else:
        st.balloons()
        st.success("Gratulujem! Ovládaš všetky otázky z tohto predmetu!")