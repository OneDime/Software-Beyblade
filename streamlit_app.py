import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE (CENTRATURA TOTALE SMARTPHONE)
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo Grigio-Blu molto scuro */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* Centratura forzata per tutti i contenitori */
    [data-testid="stVerticalBlock"] {
        text-align: center;
        align-items: center;
    }

    /* Card con bordo e colore scuro */
    .stContainer {
        border: 1px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 15px !important;
        padding: 10px !important;
    }

    /* Titolo Beyblade Centrato */
    .bey-name { 
        font-weight: bold; 
        font-size: 1.2rem; 
        color: #60a5fa; 
        text-transform: uppercase;
        margin: 10px 0;
        text-align: center;
    }

    /* Nomi Componenti Centrati */
    .comp-name {
        font-size: 1rem;
        color: #f1f5f9;
        margin-top: 15px;
        margin-bottom: 5px;
        text-align: center;
        width: 100%;
    }

    /* BOTTONI: Tutti larghi al 100% */
    .stButton > button {
        width: 100% !important;
        background-color: #334155 !important;
        color: white !important;
        border: 1px solid #475569 !important;
        height: 45px !important;
        font-size: 1rem !important;
    }
    
    /* Centratura Immagini */
    [data-testid="stImage"] img {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """, unsafe_allow_html=True)

# ... (Funzioni load_db e get_img invariate) ...
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

def add_to_inv(tipo, nome):
    if nome and nome != "n/a":
        st.session_state.inventario[tipo][nome] = st.session_state.inventario[tipo].get(nome, 0) + 1

# Inizializzazione session state se mancante
if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}

df = load_db()

# =========================
# UI PRINCIPALE (SOLO TAB AGGIUNGI)
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab1:
    search_q = st.text_input("Cerca nel database...", "").lower()
    filtered = df[df['_search'].str.contains(search_q)] if search_q else df.head(3)

    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container():
            # 1. NOME CENTRATO
            st.markdown(f"<div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
            
            # 2. IMMAGINE CENTRATA
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                st.image(img, width=180)
            
            st.write("---")

            # 3. COMPONENTI: Nome Centrato + Tasto Largo
            components = [
                ("lock_chip", "lock_bit"),
                ("blade", "blade"),
                ("main_blade", "main_blade"),
                ("assist_blade", "assist_blade"),
                ("ratchet", "ratchet"),
                ("bit", "bit"),
                ("ratchet_integrated_bit", "ratchet_integrated_bit")
            ]

            for comp_key, inv_key in components:
                val = row[comp_key]
                if val and val != "n/a":
                    # Nome componente centrato sopra il tasto
                    st.markdown(f"<div class='comp-name'>{val}</div>", unsafe_allow_html=True)
                    # Tasto "+" largo quanto la card
                    if st.button("＋", key=f"btn_{i}_{comp_key}"):
                        add_to_inv(inv_key, val)
                        st.toast(f"Aggiunto: {val}")

            st.write("---")

            # 4. TASTO AGGIUNGI TUTTO
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                for comp_key, inv_key in components:
                    val = row[comp_key]
                    if val and val != "n/a":
                        add_to_inv(inv_key, val)
                st.toast(f"Set {row['name']} aggiunto!")