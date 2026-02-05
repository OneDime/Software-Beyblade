import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

# CSS RIGIDO E ISOLATO
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* --- TAB 1: AGGIUNGI (FORCE CENTER) --- */
    /* Usiamo l'ID generato da Streamlit per la prima tab per isolare il CSS */
    #tabs-bui3-tab-0 [data-testid="stVerticalBlock"] { 
        text-align: center !important; 
        align-items: center !important; 
    }
    
    .bey-name { 
        font-weight: bold !important; 
        font-size: 1.4rem !important; 
        color: #60a5fa !important; 
        text-transform: uppercase !important; 
        margin-bottom: 8px !important; 
        text-align: center !important; 
        display: block !important;
    }
    
    .comp-name-centered { 
        font-size: 1.1rem !important; 
        color: #cbd5e1 !important; 
        margin-top: 5px !important; 
        margin-bottom: 2px !important; 
        text-align: center !important; 
        width: 100% !important; 
        display: block !important; 
    }

    /* Pulsanti Tab Aggiungi */
    #tabs-bui3-tab-0 button {
        width: auto !important; 
        min-width: 150px !important; 
        padding-left: 40px !important; 
        padding-right: 40px !important;
        height: 30px !important; 
        background-color: #334155 !important; 
        color: white !important;
        border: 1px solid #475569 !important; 
        border-radius: 4px !important; 
        font-size: 1.1rem !important;
        margin: 0 auto !important;
    }

    /* Box Beyblade */
    #tabs-bui3-tab-0 [data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 25px !important;
        padding: 15px !important;
    }

    /* --- TAB 2: INVENTARIO (FORCE LEFT) --- */
    #tabs-bui3-tab-1 [data-testid="stVerticalBlock"] { 
        text-align: left !important; 
        align-items: flex-start !important; 
    }
    
    #tabs-bui3-tab-1 [data-testid="stExpander"] { 
        text-align: left !important; 
    }
    
    #tabs-bui3-tab-1 button {
        width: 100% !important; 
        justify-content: flex-start !important; 
        background: transparent !important; 
        border: none !important; 
        color: #f1f5f9 !important; 
        text-align: left !important;
        padding-left: 10px !important;
    }

    /* --- TAB 3: DECK BUILDER --- */
    #tabs-bui3-tab-2 [data-testid="stExpander"] { 
        border: 1px solid #334155 !important; 
        background-color: #1e293b !important; 
        text-align: left !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# FUNZIONI & LOGICA
# =========================
@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame()
    df = pd.read_csv("beyblade_x.csv").fillna("")
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df

def get_img(url):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join("images", f"{h}.png")
    if os.path.exists(path): return Image.open(path)
    return None

def add_to_inv(tipo, nome, delta=1):
    if nome and nome != "n/a":
        if nome not in st.session_state.inventario[tipo]:
            st.session_state.inventario[tipo][nome] = 0
        st.session_state.inventario[tipo][nome] += delta
        if st.session_state.inventario[tipo][nome] <= 0:
            if nome in st.session_state.inventario[tipo]: del st.session_state.inventario[tipo][nome]

# Inizializzazione
if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}
if 'deck_name' not in st.session_state: st.session_state.deck_name = "IL MIO DECK"
if 'editing_name' not in st.session_state: st.session_state.editing_name = False
if 'deck_selections' not in st.session_state: st.session_state.deck_selections = {i: {} for i in range(3)}

df = load_db()

# =========================
# UI
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab1:
    search_q = st.text_input("Cerca...", "").lower()
    filtered = df[df['_search'].str.contains(search_q)] if search_q else df.head(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.markdown(f"<div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img: st.image(img, width=150)
            components = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"),
                          ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"),
                          ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            st.write("")
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                for ck, ik in components:
                    if row[ck] and row[ck] != "n/a": add_to_inv(ik, row[ck])
                st.toast("Set aggiunto!")
            st.markdown("<hr style='border-top: 1px solid #475569; margin: 15px 0;'>", unsafe_allow_html=True)
            for ck, ik in components:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name-centered'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        add_to_inv(ik, val)
                        st.toast(f"Aggiunto: {val}")

with tab2:
    modo = st.radio("Label", ["Aggiungi (+1)", "Rimuovi (-1)"], horizontal=True, label_visibility="collapsed")
    operazione = 1 if "Aggiungi" in modo else -1
    for categoria, pezzi in st.session_state.inventario.items():
        if pezzi:
            with st.expander(categoria.replace('_', ' ').upper(), expanded=False):
                for nome, qta in pezzi.items():
                    if st.button(f"{nome} x{qta}", key=f"inv_{categoria}_{nome}"):
                        add_to_inv(categoria, nome, operazione); st.rerun()

with tab3:
    with st.expander(f"{st.session_state.deck_name.upper()}", expanded=True):
        def get_options(cat, theory=False):
            if theory:
                csv_map = {"lock_bit": "lock_chip", "blade": "blade", "main_blade": "main_blade",
                           "assist_blade": "assist_blade", "ratchet": "ratchet", "bit": "bit",
                           "ratchet_integrated_bit": "ratchet_integrated_bit"}
                col_name = csv_map.get(cat, cat)
                opts = df[col_name].unique().tolist()
                return ["-"] + sorted([x for x in opts if x and x != "n/a"])
            return ["-"] + sorted(list(st.session_state.inventario[cat].keys()))

        tipologie = ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", "BX/UX Theory", "CX Theory", "BX/UX+RIB Theory", "CX+RIB Theory"]
        for idx in range(3):
            sels = st.session_state.deck_selections[idx]
            nome_parti = [v for v in sels.values() if v and v != "-"]
            titolo_slot = " ".join(nome_parti) if nome_parti else f"SLOT {idx+1}"
            with st.expander(titolo_slot.upper()):
                tipo = st.selectbox("Sistema", tipologie, key=f"type_{idx}")
                is_theory = "Theory" in tipo
                # Qui andrà la logica selectbox e immagini una volta confermato il layout