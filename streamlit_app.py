import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE "ULTRA-WIDE"
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* Centratura contenitore principale */
    [data-testid="stVerticalBlock"] {
        text-align: center;
        align-items: center;
    }

    /* CARD: Bordo e sfondo */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 30px !important;
        padding: 15px !important;
        overflow: visible !important; /* Permette ai tasti di uscire se necessario */
    }

    .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; margin-bottom: 8px; }
    .comp-name { font-size: 1.1rem; color: #cbd5e1; margin-top: 5px; margin-bottom: 2px; }

    /* IL TRUCCO PER I TASTI LARGHISSIMI */
    div[data-testid="stButton"] {
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
    }

    div.stButton > button {
        /* Forza la larghezza al 150% rispetto al suo contenitore naturale */
        width: 150% !important; 
        min-width: 150% !important;
        
        /* Traslazione per mantenerlo centrato nonostante la larghezza extra */
        transform: translateX(0%); 
        
        /* Altezza bloccata sottile */
        height: 30px !important;
        min-height: 30px !important;
        max-height: 30px !important;

        background-color: #334155 !important;
        color: white !important;
        border: 1px solid #475569 !important;
        border-radius: 4px !important;
        
        font-size: 1.1rem !important;
        line-height: 1 !important;
        padding: 0px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        
        /* Evita che il testo vada a capo */
        white-space: nowrap !important;
    }

    /* Rimuove i vincoli di larghezza dei contenitori intermedi di Streamlit */
    div[data-testid="stHorizontalBlock"], div[data-testid="stVerticalBlock"] > div {
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ... (Funzioni load_db e get_img caricate come prima) ...
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

            # AGGIUNGI TUTTO
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                for ck, ik in components:
                    if row[ck] and row[ck] != "n/a": add_to_inv(ik, row[ck])
                st.toast(f"Set aggiunto!")

            st.markdown("<hr style='border-top: 1px solid #475569; margin: 10px 0;'>", unsafe_allow_html=True)

            # TASTI SINGOLI
            for ck, ik in components:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        add_to_inv(ik, val)
                        st.toast(f"Aggiunto: {val}")