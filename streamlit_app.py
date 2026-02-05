import streamlit as st
import pandas as pd
import hashlib
import os
import json
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

# CSS per rimpicciolire card, immagini e testi
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .bey-card { 
        background-color: white; padding: 10px; border-radius: 10px; 
        border: 1px solid #ddd; margin-bottom: 10px; font-size: 0.8rem;
    }
    .bey-name { font-weight: bold; font-size: 0.9rem; color: #1e3a8a; }
    .stButton>button { width: 100%; padding: 0px; font-size: 0.7rem; }
    [data-testid="stExpander"] { border: 1px solid #e2e8f0; }
    </style>
    """, unsafe_allow_html=True)

CSV_FILE = "beyblade_x.csv"
IMAGES_DIR = "images"

# =========================
# GESTIONE MEMORIA (SESSION STATE)
# =========================
if 'inventario' not in st.session_state:
    st.session_state.inventario = {
        "lock_bit": {}, "blade": {}, "main_blade": {}, "assist_blade": {},
        "ratchet": {}, "ratchet_integrated_bit": {}, "bit": {}
    }
if 'decks' not in st.session_state:
    st.session_state.decks = []

# =========================
# FUNZIONI UTILI
# =========================
@st.cache_data
def load_db():
    if not os.path.exists(CSV_FILE): return pd.DataFrame()
    df = pd.read_csv(CSV_FILE).fillna("")
    # Creiamo una colonna di ricerca invisibile
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
# SIDEBAR
# =========================
st.sidebar.title("🔧 Officina X")
utente = st.sidebar.selectbox("Utente", ["Antonio", "Andrea", "Fabio"])
st.sidebar.divider()
if st.sidebar.button("💾 Salva Dati Online"):
    st.sidebar.info("Connessione a Google Sheets in corso...")

# =========================
# UI PRINCIPALE
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

# --- TAB 1: RICERCA E AGGIUNGI ---
with tab1:
    search_q = st.text_input("Cerca nel database (es. Aero, Dran, Flat...)", "").lower()
    
    filtered = df[df['_search'].str.contains(search_q)] if search_q else df
    
    # Griglia compatta a 4 colonne per smartphone/web
    cols = st.columns(4)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with cols[i % 4]:
            with st.container():
                st.markdown(f"<div class='bey-card'><div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
                img = get_img(row['blade_image'] or row['beyblade_page_image'])
                if img: st.image(img, width=80)
                
                # Componenti elencate (Punto 2)
                comp_list = []
                for k, label in [("lock_chip", "LB"), ("blade", "Bl"), ("ratchet", "Ra"), ("bit", "Bi")]:
                    if row[k] and row[k] != "n/a": comp_list.append(f"**{label}:** {row[k]}")
                st.markdown("<br>".join(comp_list), unsafe_allow_html=True)
                
                if st.button("➕", key=f"add_{i}"):
                    # Aggiunta intelligente di tutte le parti presenti
                    for k in ["lock_chip", "blade", "main_blade", "assist_blade", "ratchet", "ratchet_integrated_bit", "bit"]:
                        key_inv = "lock_bit" if k == "lock_chip" else k
                        if row[k] and row[k] != "n/a": add_to_inv(key_inv, row[k])
                    st.toast(f"{row['name']} aggiunto!")
                st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: INVENTARIO ---
with tab2:
    st.header(f"Magazzino di {utente}")
    inv_cols = st.columns(3)
    tipi = list(st.session_state.inventario.keys())
    for idx, tipo in enumerate(tipi):
        with inv_cols[idx % 3]:
            st.subheader(tipo.replace("_", " ").title())
            for nome, qta in st.session_state.inventario[tipo].items():
                st.write(f"**{qta}x** {nome}")

# --- TAB 3: DECK BUILDER ---
with tab3:
    col_t, col_b = st.columns([2, 1])
    col_t.header(f"Deck di {utente}")
    if col_b.button("➕ Nuovo Deck"):
        st.session_state.decks.append({"name": f"Deck {len(st.session_state.decks)+1}", "beys": [{}, {}, {}]})

    for d_idx, deck in enumerate(st.session_state.decks):
        with st.expander(f"📂 {deck['name']}", expanded=True):
            b_cols = st.columns(3)
            for b_idx in range(3):
                with b_cols[b_idx]:
                    st.markdown(f"**Beyblade {b_idx+1}**")
                    
                    # Flags (Punto 6)
                    c1, c2, c3 = st.columns(3)
                    cx = c1.checkbox("CX", key=f"cx_{d_idx}_{b_idx}")
                    rib = c2.checkbox("RIB", key=f"rib_{d_idx}_{b_idx}")
                    theory = c3.checkbox("TH", key=f"th_{d_idx}_{b_idx}", help="Usa tutto il DB")
                    
                    def get_options(key):
                        if theory: return sorted(df[key].unique().tolist())
                        inv_key = "lock_bit" if key == "lock_chip" else key
                        return sorted(list(st.session_state.inventario.get(inv_key, {}).keys()))

                    # Logica campi dinamici
                    if cx:
                        st.selectbox("Lock Bit", get_options("lock_chip"), key=f"lb_{d_idx}_{b_idx}")
                        st.selectbox("Main Blade", get_options("main_blade"), key=f"mb_{d_idx}_{b_idx}")
                        st.selectbox("Assist Blade", get_options("assist_blade"), key=f"ab_{d_idx}_{b_idx}")
                    else:
                        st.selectbox("Blade", get_options("blade"), key=f"bl_{d_idx}_{b_idx}")
                    
                    if rib:
                        st.selectbox("R.I.B.", get_options("ratchet_integrated_bit"), key=f"ri_{d_idx}_{b_idx}")
                    else:
                        st.selectbox("Ratchet", get_options("ratchet"), key=f"ra_{d_idx}_{b_idx}")
                        st.selectbox("Bit", get_options("bit"), key=f"bi_{d_idx}_{b_idx}")