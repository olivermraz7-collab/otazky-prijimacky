import streamlit as st
import json
import random

st.set_page_config(page_title="Prijímacie skúšky", page_icon="🩺", layout="centered")

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

# --- DEFINÍCIA ODBOROV A PREDMETOV ---
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

# --- INICIALIZÁCIA SESSION STATE ---
# Tu ukladáme progres pre VŠETKY predmety: { "meno_suboru.json": {"pool": [...], "score": 0, "total": 0} }
if 'subjects_data' not in st.session_state:
    st.session_state.subjects_data = {}

if 'selected_field_index' not in st.session_state:
    st.session_state.selected_field_index = 0

if 'selected_subject_name' not in st.session_state:
    st.session_state.selected_subject_name = None

# --- SIDEBAR VÝBER ---
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

# --- LOGIKA UKLADANIA A NAČÍTANIA PROGRESU ---
# Ak tento súbor ešte nemáme v pamäti, načítame ho prvýkrát
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
        st.session_state.subjects_data[selected_file] = {
            "pool": [],
            "score": 0,
            "total_count": 0
        }

# Skratka pre aktuálne dáta (referencia), aby sme nemuseli stále písať celý dlhý kľúč
current_data = st.session_state.subjects_data[selected_file]

# Tlačidlo na reset konkrétneho predmetu
if st.sidebar.button("Reštartovať aktuálny predmet"):
    del st.session_state.subjects_data[selected_file]
    st.rerun()

# --- DYNAMICKÝ NADPIS ---
if selected_field_name == "Všeobecné lekárstvo":
    st.title("🩺 Príprava na prijímačky LF")
else:
    st.title("🚑 Príprava na Urgentnú medicínu")

# --- HLAVNÝ TEST ---
pool = current_data["pool"]

if len(pool) > 0:
    q = pool[0]
    
    if q.get('repetition_mode'):
        st.info("🔄 OPAKOVANIE CHYBY")

    st.subheader(f"Otázka č. {q['id']}")
    st.write(q['text'])

    user_choices = []
    # Formulár musí mať unikátny kľúč, aby Streamlit vedel, že ide o iný formulár pri prepnutí predmetu
    with st.form(key=f"form_{selected_file}_{q['id']}"):
        for opt in q['options']:
            if st.checkbox(opt, key=f"cb_{selected_file}_{q['id']}_{opt}"):
                user_choices.append(opt[0])

        submit_button = st.form_submit_button(label='Overiť odpoveď')

    if submit_button:
        user_str = "".join(sorted(user_choices))
        correct_str = "".join(sorted(q['answer']))

        if user_str == correct_str:
            st.success(f"✅ SPRÁVNE! (Odpoveď: {q['answer']})")
            
            if q.get('repetition_mode'):
                q_to_move = pool.pop(0)
                new_index = min(9, len(pool)) 
                pool.insert(new_index, q_to_move)
                st.info(f"Výborne! Táto otázka sa znova objaví o {new_index+1} miest.")
            else:
                pool.pop(0)
                current_data["score"] += 1
        else:
            st.error(f"❌ NESPRÁVNE! Správna odpoveď: {q['answer']}")
            wrong_q = pool.pop(0)
            wrong_q['repetition_mode'] = True
            new_index = min(4, len(pool))
            pool.insert(new_index, wrong_q)
            st.warning(f"Chyba. Posunuté o {new_index+1} miest.")

        if st.button("Pokračovať"):
            st.rerun()
    
    # Štatistiky
    st.sidebar.divider()
    st.sidebar.write(f"🎓 Odbor: **{selected_field_name}**")
    st.sidebar.write(f"📊 Správne (na 1. pokus): **{current_data['score']}**")
    st.sidebar.write(f"⏳ Zostáva v obehu: **{len(pool)}** / {current_data['total_count']}")
    
else:
    if current_data["total_count"] == 0:
        st.warning(f"Súbor `{selected_file}` je prázdny alebo neexistuje.")
    else:
        st.balloons()
        st.success(f"Hotovo! Prešiel si všetky otázky z predmetu {subject_display_name}!")
