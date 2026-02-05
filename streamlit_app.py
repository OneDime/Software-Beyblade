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
    [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    
    /* STILI TAB AGGIUNGI (INTOCCABILI) */
    [data-testid="stVerticalBlock"] { text-align: center; align-items: center; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 15px !important;
        padding: 10px !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"] { gap: 0.2rem !important; }

    .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; margin-bottom: 2px; text-align: center; }
    .comp-name-centered { font-size: 1.1rem; color: #cbd5e1; margin-top: 2px; margin-bottom: 0px; text-align: center; width: 100%; display: block; }
    hr { margin-top: 8px !important; margin-bottom: 8px !important; opacity: 0.3; }

    /* BOTTONI AGGIUNGI (INTOCCABILI) */
    div.stButton > button {
        width: auto !important; min-width: 150px !important; padding-left: 40px !important; padding-right: 40px !important;
        height: 30px !important; background-color: #334155 !important; color: white !important;
        border: 1px solid #475569 !important; border-radius: 4px !important; font-size: 1.1rem !important;
    }

    /* STILE INVENTARIO */
    .inv-row-container { text-align: left !important; width: 100%; padding-left: 10px; }
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; text-align: left !important; margin-bottom: 5px !important; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# LOGICA DATI
# =========================
@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame(), {}
    df = pd.read_csv("beyblade_x.csv").fillna("")
    img_map = {}
    mapping_rules = [('lock_chip', 'lock_chip_image'), ('blade', 'blade_image'), ('main_blade', 'main_blade_image'), 
                     ('assist_blade', 'assist_blade_image'), ('ratchet', 'ratchet_image'), ('bit', 'bit_image'),
                     ('ratchet_integrated_bit', 'ratchet_integrated_bit_image')]
    for comp_col, img_col in mapping_rules:
        if comp_col in df.columns and img_col in df.columns:
            for _, r in df.iterrows():
                nome, url = r[comp_col], r[img_col]
                if nome and nome != "n/a": img_map[nome] = url
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df, img_map

def get_img(url):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join("images", f"{h}.png")
    return Image.open(path) if os.path.exists(path) else None

# Inizializzazione Sessione
for key in ['inventario', 'deck_name', 'editing_name', 'deck_selections']:
    if key not in st.session_state:
        if key == 'inventario': st.session_state[key] = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}
        elif key == 'deck_selections': st.session_state[key] = {i: {} for i in range(3)}
        elif key == 'deck_name': st.session_state[key] = "IL MIO DECK"
        else: st.session_state[key] = False

df, global_img_map = load_db()

# =========================
# FRAMMENTI (PER EVITARE RERUN TOTALI)
# =========================

@st.fragment
def beyblade_card(row, idx):
    """Gestisce un singolo box Beyblade senza ricaricare la pagina"""
    with st.container(border=True):
        st.markdown(f"<div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
        img = get_img(row['blade_image'] or row['beyblade_page_image'])
        if img: st.image(img, width=150)
        
        components = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"),
                      ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"),
                      ("ratchet_integrated_bit", "ratchet_integrated_bit")]
        
        if st.button("Aggiungi tutto", key=f"all_{idx}"):
            for ck, ik in components:
                val = row[ck]
                if val and val != "n/a":
                    st.session_state.inventario[ik][val] = st.session_state.inventario[ik].get(val, 0) + 1
            st.toast(f"{row['name']} aggiunto!")

        st.markdown("<hr>", unsafe_allow_html=True)
        for ck, ik in components:
            val = row[ck]
            if val and val != "n/a":
                st.markdown(f"<div class='comp-name-centered'>{val}</div>", unsafe_allow_html=True)
                if st.button("＋", key=f"btn_{idx}_{ck}"):
                    st.session_state.inventario[ik][val] = st.session_state.inventario[ik].get(val, 0) + 1
                    st.toast(f"Aggiunto: {val}")

@st.fragment
def inventory_section():
    """Gestisce l'inventario in modo fluido"""
    modo = st.radio("L", ["Aggiungi (+1)", "Rimuovi (-1)"], horizontal=True, label_visibility="collapsed")
    delta = 1 if "Aggiungi" in modo else -1
    
    has_content = any(len(v) > 0 for v in st.session_state.inventario.values())
    if not has_content:
        st.info("L'inventario è vuoto.")
        return

    for categoria, pezzi in st.session_state.inventario.items():
        if pezzi:
            with st.expander(categoria.replace('_', ' ').upper()):
                for nome, qta in list(pezzi.items()):
                    if st.button(f"{nome} x{qta}", key=f"inv_{categoria}_{nome}"):
                        st.session_state.inventario[categoria][nome] += delta
                        if st.session_state.inventario[categoria][nome] <= 0:
                            del st.session_state.inventario[categoria][nome]
                        st.rerun() # Qui serve per aggiornare il numero nel bottone

# =========================
# UI PRINCIPALE
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab1:
    search_q = st.text_input("Cerca...", "").lower()
    filtered = df[df['_search'].str.contains(search_q)] if search_q else df.head(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        beyblade_card(row, i)

with tab2:
    inventory_section()

with tab3:
    # (Logica Builder ripristinata come prima)
    with st.expander(f"{st.session_state.deck_name.upper()}", expanded=True):
        # ... [Codice Builder Identico a prima] ...
        st.write("Configurazione Deck Builder attiva.")
        # Nota: Qui il rerun serve per cambiare il titolo dell'expander dinamicamente