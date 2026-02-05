import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

# CSS BASE (Sfondo e colori generali)
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
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

def add_to_inv(tipo, nome, delta=1):
    if nome and nome != "n/a":
        if nome not in st.session_state.inventario[tipo]:
            st.session_state.inventario[tipo][nome] = 0
        st.session_state.inventario[tipo][nome] += delta
        if st.session_state.inventario[tipo][nome] <= 0:
            if nome in st.session_state.inventario[tipo]: del st.session_state.inventario[tipo][nome]

if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}
if 'deck_name' not in st.session_state: st.session_state.deck_name = "IL MIO DECK"
if 'editing_name' not in st.session_state: st.session_state.editing_name = False
if 'deck_selections' not in st.session_state: st.session_state.deck_selections = {i: {} for i in range(3)}

df = load_db()

# =========================
# UI PRINCIPALE
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

# --- TAB 1: AGGIUNGI (FORCE CENTER) ---
with tab1:
    # Iniettiamo il CSS SOLO per questa tab usando un container dedicato
    st.markdown("""
        <style>
        .container-aggiungi [data-testid="stVerticalBlock"] { text-align: center !important; align-items: center !important; }
        .container-aggiungi div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 2px solid #334155 !important; background-color: #1e293b !important;
            border-radius: 12px !important; margin-bottom: 25px !important; padding: 15px !important;
        }
        .bey-name { font-weight: bold !important; font-size: 1.4rem !important; color: #60a5fa !important; text-transform: uppercase !important; text-align: center !important; display: block !important; }
        .comp-name-centered { font-size: 1.1rem !important; color: #cbd5e1 !important; text-align: center !important; width: 100% !important; display: block !important; }
        .container-aggiungi button { width: auto !important; min-width: 150px !important; background-color: #334155 !important; color: white !important; }
        </style>
        """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="container-aggiungi">', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: INVENTARIO (FORCE LEFT) ---
with tab2:
    st.markdown("""
        <style>
        .container-inventario [data-testid="stVerticalBlock"] { text-align: left !important; align-items: flex-start !important; }
        .container-inventario button { width: 100% !important; justify-content: flex-start !important; text-align: left !important; background: transparent !important; border: none !important; }
        </style>
        """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="container-inventario">', unsafe_allow_html=True)
        modo = st.radio("M", ["Aggiungi (+1)", "Rimuovi (-1)"], horizontal=True, label_visibility="collapsed")
        operazione = 1 if "Aggiungi" in modo else -1
        for categoria, pezzi in st.session_state.inventario.items():
            if pezzi:
                with st.expander(categoria.replace('_', ' ').upper(), expanded=False):
                    for nome, qta in pezzi.items():
                        if st.button(f"{nome} x{qta}", key=f"inv_{categoria}_{nome}"):
                            add_to_inv(categoria, nome, operazione); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: DECK BUILDER ---
with tab3:
    st.markdown('<div class="container-builder">', unsafe_allow_html=True)
    # Qui il builder rimane con l'allineamento standard (sinistra per le select)
    with st.expander(f"{st.session_state.deck_name.upper()}", expanded=True):
        # ... (Logica Builder come prima)
        st.write("Pronto per le modifiche al builder.")
    st.markdown('</div>', unsafe_allow_html=True)