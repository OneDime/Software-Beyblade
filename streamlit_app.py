import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* CARD: Bordo e sfondo */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 25px !important;
        padding: 15px !important;
    }

    .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; margin-bottom: 8px; text-align: center; }
    .comp-name-centered { font-size: 1.1rem; color: #cbd5e1; margin-top: 5px; margin-bottom: 2px; text-align: center; width: 100%; display: block; }

    /* BOTTONI TAB AGGIUNGI (INTOCCABILI) */
    div.stButton > button {
        width: auto !important; 
        min-width: 150px !important; 
        padding-left: 40px !important;  
        padding-right: 40px !important;
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

    /* STILE TASTI INVENTARIO (ALLINEATI A SINISTRA) */
    .inv-button button {
        width: 100% !important;
        justify-content: flex-start !important;
        padding-left: 10px !important;
        background: transparent !important;
        border: none !important;
        color: #f1f5f9 !important;
        text-align: left !important;
        font-size: 1.1rem !important;
    }
    
    .inv-button button:hover {
        background: #334155 !important;
    }

    /* Rimuove icona e stile expander */
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# FUNZIONI UTILI
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

def add_to_inv(tipo, nome, qta=1):
    if nome and nome != "n/a":
        if nome not in st.session_state.inventario[tipo]:
            st.session_state.inventario[tipo][nome] = 0
        st.session_state.inventario[tipo][nome] += qta
        # Rimuove se arriva a 0
        if st.session_state.inventario[tipo][nome] <= 0:
            del st.session_state.inventario[tipo][nome]

if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}

df = load_db()

# =========================
# UI PRINCIPALE
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "Inventario", "🧩 Deck Builder"])

# --- TAB 1: AGGIUNGI (INTOCCABILE) ---
with tab1:
    search_q = st.text_input("Cerca...", "").lower()
    filtered = df[df['_search'].str.contains(search_q)] if search_q else df.head(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.markdown(f"<div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                c_img = st.columns([1, 2, 1])
                with c_img[1]: st.image(img, use_container_width=True)
            
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

# --- TAB 2: INVENTARIO (CLICK PER +1, PULSANTE PER -1) ---
with tab2:
    has_content = any(any(q > 0 for q in p.values()) for p in st.session_state.inventario.values())
            
    if not has_content:
        st.info("L'inventario è vuoto.")
    else:
        for categoria, pezzi in st.session_state.inventario.items():
            if pezzi:
                cat_label = categoria.replace('_', ' ').upper()
                with st.expander(cat_label, expanded=False):
                    for nome, qta in pezzi.items():
                        col_text, col_opt = st.columns([0.8, 0.2])
                        
                        # Click sul nome per aumentare +1
                        with col_text:
                            st.markdown('<div class="inv-button">', unsafe_allow_html=True)
                            if st.button(f"{nome} x{qta}", key=f"add_{categoria}_{nome}"):
                                add_to_inv(categoria, nome, 1)
                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Piccolo tasto per diminuire -1
                        with col_opt:
                            if st.button("－", key=f"del_{categoria}_{nome}"):
                                add_to_inv(categoria, nome, -1)
                                st.rerun()

# --- TAB 3: DECK BUILDER ---
with tab3:
    st.info("Area Deck Builder in fase di allestimento...")