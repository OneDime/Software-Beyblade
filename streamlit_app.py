import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE (TASTI PROPORZIONATI AL TESTO)
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo Grigio-Blu molto scuro */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* Centratura forzata */
    [data-testid="stVerticalBlock"] {
        text-align: center;
        align-items: center;
    }

    /* CARD: Bordo e sfondo */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 25px !important;
        padding: 15px !important;
    }

    .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; margin-bottom: 8px; text-align: center; }
    .comp-name { font-size: 1.1rem; color: #cbd5e1; margin-top: 5px; margin-bottom: 2px; text-align: center; }

    /* TASTI: Proporzionati al testo, larghi 1.5x e alti 30px */
    div[data-testid="stButton"] {
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
    }

    div.stButton > button {
        /* Larghezza basata sul contenuto (testo) */
        width: auto !important; 
        min-width: 150px !important; /* Minimo per non farlo troppo stretto sul "+" */
        padding-left: 40px !important;  /* Padding generoso per caricarlo lateralmente */
        padding-right: 40px !important;
        
        /* Altezza bloccata a 30px */
        height: 30px !important;
        min-height: 30px !important;
        max-height: 30px !important;

        background-color: #334155 !important;
        color: white !important;
        border: 1px solid #475569 !important;
        border-radius: 4px !important;
        
        font-size: 1.1rem !important;
        line-height: 1 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        white-space: nowrap !important;
    }

    /* Riduzione spazio tra gli elementi */
    .stMarkdown { margin-bottom: -10px !important; }
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

if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}

df = load_db()

# =========================
# UI PRINCIPALE
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
            
            components = [
                ("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"),
                ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"),
                ("ratchet_integrated_bit", "ratchet_integrated_bit")
            ]

            # AGGIUNGI TUTTO (1.5x rispetto alla scritta)
            st.write("")
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                for ck, ik in components:
                    if row[ck] and row[ck] != "n/a": add_to_inv(ik, row[ck])
                st.toast(f"Set aggiunto!")

            st.markdown("<hr style='border-top: 1px solid #475569; margin: 15px 0;'>", unsafe_allow_html=True)

            # TASTI SINGOLI
            for ck, ik in components:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        add_to_inv(ik, val)
                        st.toast(f"Aggiunto: {val}")