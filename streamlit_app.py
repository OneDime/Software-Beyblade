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
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 15px !important;
        padding: 10px !important;
    }
    .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; text-align: center; }
    .comp-name-centered { font-size: 1.1rem; color: #cbd5e1; text-align: center; width: 100%; display: block; }
    
    /* BOTTONI AGGIUNGI (INTOCCABILI) */
    div.stButton > button {
        width: auto !important; min-width: 150px !important;
        height: 30px !important; background-color: #334155 !important; color: white !important;
        border: 1px solid #475569 !important; border-radius: 4px !important;
    }

    /* STILE DECK BUILDER & EXPANDER */
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; margin-bottom: 5px !important; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# LOGICA DATI & IMMAGINI
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

def get_img(url, size=(100, 100)):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join("images", f"{h}.png")
    if os.path.exists(path):
        img = Image.open(path)
        return img.resize(size, Image.Resampling.LANCZOS)
    return None

# =========================
# INIZIALIZZAZIONE SESSIONE
# =========================
if 'inventario' not in st.session_state: 
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}

# Gestione Multi-Deck
if 'decks' not in st.session_state:
    st.session_state.decks = {"DECK 1": {i: {} for i in range(3)}}
if 'current_deck' not in st.session_state:
    st.session_state.current_deck = "DECK 1"
if 'expander_state' not in st.session_state:
    st.session_state.expander_state = {i: False for i in range(3)}
if 'editing_name' not in st.session_state:
    st.session_state.editing_name = False

df, global_img_map = load_db()

# =========================
# UI PRINCIPALE
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

# TAB 1 & 2 (Invariate come da accordi)
with tab1:
    search_q = st.text_input("Cerca...", "").lower()
    filtered = df[df['_search'].str.contains(search_q)] if search_q else df.head(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.markdown(f"<div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
            img = get_img(row['blade_image'] or row['beyblade_page_image'], size=(150, 150))
            if img: st.image(img)
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                for ck, ik in [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), ("ratchet_integrated_bit", "ratchet_integrated_bit")]:
                    val = row[ck]
                    if val and val != "n/a": st.session_state.inventario[ik][val] = st.session_state.inventario[ik].get(val, 0) + 1
                st.toast("Aggiunto!")

with tab2:
    for categoria, pezzi in st.session_state.inventario.items():
        if pezzi:
            with st.expander(categoria.replace('_', ' ').upper()):
                for nome, qta in pezzi.items():
                    st.write(f"{nome} x{qta}")

# --- TAB 3: DECK BUILDER (RIPRISTINATO MULTI-DECK) ---
with tab3:
    # Selezione e Creazione Deck
    col_sel, col_add = st.columns([0.8, 0.2])
    deck_list = list(st.session_state.decks.keys())
    
    st.session_state.current_deck = col_sel.selectbox("Seleziona Deck", deck_list, index=deck_list.index(st.session_state.current_deck))
    
    if col_add.button("➕ Nuovo Deck"):
        new_id = len(st.session_state.decks) + 1
        name = f"DECK {new_id}"
        st.session_state.decks[name] = {i: {} for i in range(3)}
        st.session_state.current_deck = name
        st.rerun()

    # Opzioni Deck Corrente
    curr_deck_data = st.session_state.decks[st.session_state.current_deck]
    
    with st.expander(f"GESTIONE: {st.session_state.current_deck.upper()}", expanded=True):
        
        # Logica per ogni Slot
        def get_options(cat, theory=False):
            if theory:
                csv_map = {"lock_bit": "lock_chip", "blade": "blade", "main_blade": "main_blade", "assist_blade": "assist_blade", "ratchet": "ratchet", "bit": "bit", "ratchet_integrated_bit": "ratchet_integrated_bit"}
                return ["-"] + sorted([x for x in df[csv_map.get(cat, cat)].unique().tolist() if x and x != "n/a"])
            return ["-"] + sorted(list(st.session_state.inventario[cat].keys()))

        tipologie = ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", "BX/UX Theory", "CX Theory", "BX/UX+RIB Theory", "CX+RIB Theory"]

        for idx in range(3):
            sels = curr_deck_data[idx]
            nome_parti = [v for v in sels.values() if v and v != "-"]
            titolo_slot = " ".join(nome_parti) if nome_parti else f"SLOT {idx+1}"
            
            with st.expander(titolo_slot.upper(), expanded=st.session_state.expander_state[idx]):
                tipo = st.selectbox("Sistema", tipologie, key=f"type_{st.session_state.current_deck}_{idx}")
                is_theory = "Theory" in tipo
                curr = {}

                # Configurazione Slot
                if "BX/UX" in tipo and "+RIB" not in tipo:
                    curr['b'] = st.selectbox("Blade", get_options("blade", is_theory), key=f"b_{idx}_{st.session_state.current_deck}")
                    curr['r'] = st.selectbox("Ratchet", get_options("ratchet", is_theory), key=f"r_{idx}_{st.session_state.current_deck}")
                    curr['bi'] = st.selectbox("Bit", get_options("bit", is_theory), key=f"bi_{idx}_{st.session_state.current_deck}")
                # ... (Logica CX e RIB identica alle versioni precedenti)
                elif "CX" in tipo and "+RIB" not in tipo:
                    curr['lb'] = st.selectbox("Lock Bit", get_options("lock_bit", is_theory), key=f"lb_{idx}_{st.session_state.current_deck}")
                    curr['mb'] = st.selectbox("Main Blade", get_options("main_blade", is_theory), key=f"mb_{idx}_{st.session_state.current_deck}")
                    curr['ab'] = st.selectbox("Assist Blade", get_options("assist_blade", is_theory), key=f"ab_{idx}_{st.session_state.current_deck}")
                    curr['r'] = st.selectbox("Ratchet", get_options("ratchet", is_theory), key=f"r_{idx}_{st.session_state.current_deck}")
                    curr['bi'] = st.selectbox("Bit", get_options("bit", is_theory), key=f"bi_{idx}_{st.session_state.current_deck}")
                elif "BX/UX+RIB" in tipo:
                    curr['b'] = st.selectbox("Blade", get_options("blade", is_theory), key=f"b_{idx}_{st.session_state.current_deck}")
                    curr['rib'] = st.selectbox("RIB", get_options("ratchet_integrated_bit", is_theory), key=f"rib_{idx}_{st.session_state.current_deck}")
                elif "CX+RIB" in tipo:
                    curr['lb'] = st.selectbox("Lock Bit", get_options("lock_bit", is_theory), key=f"lb_{idx}_{st.session_state.current_deck}")
                    curr['mb'] = st.selectbox("Main Blade", get_options("main_blade", is_theory), key=f"mb_{idx}_{st.session_state.current_deck}")
                    curr['ab'] = st.selectbox("Assist Blade", get_options("assist_blade", is_theory), key=f"ab_{idx}_{st.session_state.current_deck}")
                    curr['rib'] = st.selectbox("RIB", get_options("ratchet_integrated_bit", is_theory), key=f"rib_{idx}_{st.session_state.current_deck}")

                # Immagini forzate 100x100
                st.write("")
                cols = st.columns(5)
                for i, (k, v) in enumerate(curr.items()):
                    if v != "-":
                        url = global_img_map.get(v)
                        img_obj = get_img(url, size=(100, 100))
                        if img_obj: cols[i].image(img_obj)

                if curr_deck_data[idx] != curr:
                    curr_deck_data[idx] = curr
                    st.session_state.expander_state[idx] = True
                    st.rerun()

        # Footer Gestione Deck
        st.markdown("---")
        c1, c2, c3 = st.columns([0.3, 0.3, 0.4])
        
        if c1.button("📝 Rinomina Deck"):
            st.session_state.editing_name = True
            
        if c2.button("🗑️ Elimina Deck", type="primary"):
            if len(st.session_state.decks) > 1:
                del st.session_state.decks[st.session_state.current_deck]
                st.session_state.current_deck = list(st.session_state.decks.keys())[0]
                st.rerun()
            else:
                st.error("Non puoi eliminare l'ultimo deck!")

        if st.session_state.editing_name:
            new_name = st.text_input("Nuovo nome:", st.session_state.current_deck)
            if st.button("Conferma Rinomina"):
                st.session_state.decks[new_name] = st.session_state.decks.pop(st.session_state.current_deck)
                st.session_state.current_deck = new_name
                st.session_state.editing_name = False
                st.rerun()