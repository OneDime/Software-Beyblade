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

    /* STILE EXPANDER */
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; text-align: left !important; margin-bottom: 5px !important; }
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
if 'decks' not in st.session_state:
    st.session_state.decks = [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]
if 'exp_state' not in st.session_state:
    st.session_state.exp_state = {}
if 'edit_name_idx' not in st.session_state:
    st.session_state.edit_name_idx = None

df, global_img_map = load_db()

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
            img = get_img(row['blade_image'] or row['beyblade_page_image'], size=(150, 150))
            if img: st.image(img)
            components = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"),
                          ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"),
                          ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                for ck, ik in components:
                    val = row[ck]
                    if val and val != "n/a": st.session_state.inventario[ik][val] = st.session_state.inventario[ik].get(val, 0) + 1
                st.toast("Aggiunto!")
            st.markdown("<hr>", unsafe_allow_html=True)
            for ck, ik in components:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name-centered'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        st.session_state.inventario[ik][val] = st.session_state.inventario[ik].get(val, 0) + 1
                        st.toast(f"Aggiunto: {val}")

with tab2:
    modo = st.radio("L", ["Aggiungi (+1)", "Rimuovi (-1)"], horizontal=True, label_visibility="collapsed")
    operazione = 1 if "Aggiungi" in modo else -1
    for categoria, pezzi in st.session_state.inventario.items():
        if pezzi:
            with st.expander(categoria.replace('_', ' ').upper()):
                for nome, qta in pezzi.items():
                    if st.button(f"{nome} x{qta}", key=f"inv_{categoria}_{nome}"):
                        st.session_state.inventario[categoria][nome] += operazione
                        if st.session_state.inventario[categoria][nome] <= 0: del st.session_state.inventario[categoria][nome]
                        st.rerun()

with tab3:
    def get_options(cat, theory=False):
        if theory:
            csv_map = {"lock_bit": "lock_chip", "blade": "blade", "main_blade": "main_blade", "assist_blade": "assist_blade", "ratchet": "ratchet", "bit": "bit", "ratchet_integrated_bit": "ratchet_integrated_bit"}
            return ["-"] + sorted([x for x in df[csv_map.get(cat, cat)].unique().tolist() if x and x != "n/a"])
        return ["-"] + sorted(list(st.session_state.inventario[cat].keys()))

    tipologie = ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", "BX/UX Theory", "CX Theory", "BX/UX+RIB Theory", "CX+RIB Theory"]

    for d_idx, deck in enumerate(st.session_state.decks):
        # Expander principale del Deck (Niente icone)
        with st.expander(f"{deck['name'].upper()}", expanded=True):
            for s_idx in range(3):
                sels = deck["slots"][s_idx]
                nome_parti = [v for v in sels.values() if v and v != "-"]
                titolo_slot = " ".join(nome_parti) if nome_parti else f"SLOT {s_idx+1}"
                exp_key = f"{d_idx}-{s_idx}"
                
                with st.expander(titolo_slot.upper(), expanded=st.session_state.exp_state.get(exp_key, False)):
                    tipo = st.selectbox("Sistema", tipologie, key=f"type_{d_idx}_{s_idx}")
                    is_theory = "Theory" in tipo
                    curr = {}

                    if "BX/UX" in tipo and "+RIB" not in tipo:
                        curr['b'] = st.selectbox("Blade", get_options("blade", is_theory), key=f"b_{d_idx}_{s_idx}")
                        curr['r'] = st.selectbox("Ratchet", get_options("ratchet", is_theory), key=f"r_{d_idx}_{s_idx}")
                        curr['bi'] = st.selectbox("Bit", get_options("bit", is_theory), key=f"bi_{d_idx}_{s_idx}")
                    elif "CX" in tipo and "+RIB" not in tipo:
                        curr['lb'] = st.selectbox("Lock Bit", get_options("lock_bit", is_theory), key=f"lb_{d_idx}_{s_idx}")
                        curr['mb'] = st.selectbox("Main Blade", get_options("main_blade", is_theory), key=f"mb_{d_idx}_{s_idx}")
                        curr['ab'] = st.selectbox("Assist Blade", get_options("assist_blade", is_theory), key=f"ab_{d_idx}_{s_idx}")
                        curr['r'] = st.selectbox("Ratchet", get_options("ratchet", is_theory), key=f"r_{d_idx}_{s_idx}")
                        curr['bi'] = st.selectbox("Bit", get_options("bit", is_theory), key=f"bi_{d_idx}_{s_idx}")
                    elif "BX/UX+RIB" in tipo:
                        curr['b'] = st.selectbox("Blade", get_options("blade", is_theory), key=f"b_{d_idx}_{s_idx}")
                        curr['rib'] = st.selectbox("RIB", get_options("ratchet_integrated_bit", is_theory), key=f"rib_{d_idx}_{s_idx}")
                    elif "CX+RIB" in tipo:
                        curr['lb'] = st.selectbox("Lock Bit", get_options("lock_bit", is_theory), key=f"lb_{d_idx}_{s_idx}")
                        curr['mb'] = st.selectbox("Main Blade", get_options("main_blade", is_theory), key=f"mb_{d_idx}_{s_idx}")
                        curr['ab'] = st.selectbox("Assist Blade", get_options("assist_blade", is_theory), key=f"ab_{d_idx}_{s_idx}")
                        curr['rib'] = st.selectbox("RIB", get_options("ratchet_integrated_bit", is_theory), key=f"rib_{d_idx}_{s_idx}")

                    st.write("")
                    cols = st.columns(5)
                    for i, (k, v) in enumerate(curr.items()):
                        if v != "-":
                            url = global_img_map.get(v)
                            img_obj = get_img(url, size=(100, 100))
                            if img_obj: cols[i].image(img_obj)

                    if deck["slots"][s_idx] != curr:
                        deck["slots"][s_idx] = curr
                        st.session_state.exp_state[exp_key] = True
                        st.rerun()
            
            # Comandi in fondo all'expander del deck
            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2, _ = st.columns([0.2, 0.2, 0.6])
            if c1.button("📝 Rinomina", key=f"ren_{d_idx}"):
                st.session_state.edit_name_idx = d_idx
                st.rerun()
            if c2.button("🗑️ Elimina", key=f"del_{d_idx}", type="primary"):
                if len(st.session_state.decks) > 1:
                    st.session_state.decks.pop(d_idx)
                    st.rerun()
            
            if st.session_state.edit_name_idx == d_idx:
                new_n = st.text_input("Nuovo nome:", deck['name'], key=f"input_{d_idx}")
                if st.button("Salva", key=f"save_{d_idx}"):
                    deck['name'] = new_n
                    st.session_state.edit_name_idx = None
                    st.rerun()

    st.markdown("---")
    if st.button("➕ Aggiungi Nuovo Deck"):
        st.session_state.decks.append({"name": f"DECK {len(st.session_state.decks) + 1}", "slots": {i: {} for i in range(3)}})
        st.rerun()