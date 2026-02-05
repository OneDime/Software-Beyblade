import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE (FOCUS SMARTPHONE)
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo Grigio-Blu molto scuro */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* Card Centrata */
    .bey-card { 
        background-color: #1e293b; 
        padding: 15px; 
        border-radius: 15px; 
        border: 1px solid #334155; 
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* Titolo Beyblade Centrato */
    .bey-name { 
        font-weight: bold; 
        font-size: 1.1rem; 
        color: #60a5fa; 
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    /* Centratura Immagini */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }

    /* Tabella Componenti centrata */
    .comp-table {
        width: 100%;
        margin: 10px 0;
        border-collapse: collapse;
    }
    .comp-table td {
        padding: 4px;
        vertical-align: middle;
    }

    /* Bottone "+" e "Aggiungi tutto" */
    .stButton > button {
        background-color: #334155 !important;
        color: white !important;
        border: 1px solid #475569 !important;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

CSV_FILE = "beyblade_x.csv"
IMAGES_DIR = "images"

# =========================
# GESTIONE MEMORIA
# =========================
if 'inventario' not in st.session_state:
    st.session_state.inventario = {
        "lock_bit": {}, "blade": {}, "main_blade": {}, "assist_blade": {},
        "ratchet": {}, "ratchet_integrated_bit": {}, "bit": {}
    }

# =========================
# FUNZIONI UTILI
# =========================
@st.cache_data
def load_db():
    if not os.path.exists(CSV_FILE): return pd.DataFrame()
    df = pd.read_csv(CSV_FILE).fillna("")
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df

def get_img(url):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join(IMAGES_DIR, f"{h}.png")
    if os.path.exists(path): return Image.open(path)
    return None

def add_to_inv(tipo, nome):
    if nome and nome != "n/a":
        st.session_state.inventario[tipo][nome] = st.session_state.inventario[tipo].get(nome, 0) + 1

df = load_db()

# =========================
# UI PRINCIPALE
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab1:
    search_q = st.text_input("Cerca nel database...", "").lower()
    filtered = df[df['_search'].str.contains(search_q)] if search_q else df.head(5)

    for i, (_, row) in enumerate(filtered.iterrows()):
        # Utilizzo di una card centrata per ogni Beyblade
        with st.container(border=True):
            # 1. TABELLA NOME (Centrato)
            st.markdown(f"<div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
            
            # 2. TABELLA IMMAGINE (Centrata)
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                st.image(img, width=150)
            
            st.divider()

            # 3. TABELLA COMPONENTI: Nome a sinistra, Tasto "+" a destra
            # Per garantire la centratura orizzontale su mobile, usiamo le colonne ma allineate
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
                    # Creiamo una riga per ogni componente
                    c1, c2 = st.columns([0.8, 0.2])
                    c1.markdown(f"<div style='text-align: right; padding-top: 5px;'>{val}</div>", unsafe_allow_html=True)
                    if c2.button("＋", key=f"btn_{i}_{comp_key}"):
                        add_to_inv(inv_key, val)
                        st.toast(f"Aggiunto: {val}")

            st.write("") # Spazio

            # 4. TASTO AGGIUNGI TUTTO (Largo quanto la card)
            if st.button("Aggiungi tutto", key=f"all_{i}", use_container_width=True):
                for comp_key, inv_key in components:
                    val = row[comp_key]
                    if val and val != "n/a":
                        add_to_inv(inv_key, val)
                st.toast(f"Tutti i componenti di {row['name']} aggiunti!")

# TAB 2 e 3 restano momentaneamente invariati come da tua base