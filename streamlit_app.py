import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE (TASTI COMPATTI 30PX)
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo Grigio-Blu molto scuro */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* Centratura forzata di tutti gli elementi */
    [data-testid="stVerticalBlock"] {
        text-align: center;
        align-items: center;
    }

    /* CARD: Bordo e distanziamento */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 25px !important;
        padding: 15px !important;
    }

    /* Titolo Beyblade Centrato */
    .bey-name { 
        font-weight: bold; 
        font-size: 1.3rem; 
        color: #60a5fa; 
        text-transform: uppercase;
        margin-bottom: 8px;
        text-align: center;
    }

    /* Nomi Componenti Centrati */
    .comp-name {
        font-size: 0.95rem;
        color: #cbd5e1;
        margin-top: 12px;
        margin-bottom: 4px;
        text-align: center;
        width: 100%;
        display: block;
    }

    /* BOTTONI LARGHI AL 100% - Altezza 30px */
    div.stButton > button {
        width: 100% !important;
        display: block !important;
        background-color: #334155 !important;
        color: white !important;
        border: 1px solid #475569 !important;
        height: 30px !important; /* Ridotto a 30px come richiesto */
        font-size: 0.9rem !important;
        border-radius: 4px !important;
        line-height: 1 !important;
        padding: 0 !important;
    }
    
    /* Centratura Immagini */
    [data-testid="stImage"] img {
        display: block;
        margin: 0 auto;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# FUNZIONI CORE
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

def add_to_inv(tipo, nome):
    if nome and nome != "n/a":
        st.session_state.inventario[tipo][nome] = st.session_state.inventario[tipo].get(nome, 0) + 1

if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}

df = load_db()

# =========================
# UI PRINCIPALE
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab1:
    search_q = st.text_input("Cerca nel database...", "").lower()
    filtered = df[df['_search'].str.contains(search_q)] if search_q else df.head(3)

    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            # 1. NOME CENTRATO
            st.markdown(f"<div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
            
            # 2. IMMAGINE CENTRATA
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                st.image(img, width=150)
            
            # 3. TASTO AGGIUNGI TUTTO (30px)
            components = [
                ("lock_chip", "lock_bit"),
                ("blade", "blade"),
                ("main_blade", "main_blade"),
                ("assist_blade", "assist_blade"),
                ("ratchet", "ratchet"),
                ("bit", "bit"),
                ("ratchet_integrated_bit", "ratchet_integrated_bit")
            ]

            st.write("") 
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                for comp_key, inv_key in components:
                    val = row[comp_key]
                    if val and val != "n/a":
                        add_to_inv(inv_key, val)
                st.toast(f"Set {row['name']} aggiunto!")

            st.markdown("<hr style='border-top: 1px solid #475569; width: 100%; margin: 12px 0;'>", unsafe_allow_html=True)

            # 4. COMPONENTI SINGOLI (Tasti 30px)
            for comp_key, inv_key in components:
                val = row[comp_key]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{comp_key}"):
                        add_to_inv(inv_key, val)
                        st.toast(f"Aggiunto: {val}")