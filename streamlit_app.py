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
    
    /* RIDUZIONE SPAZIO VERTICALE GLOBALE */
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

    /* STILE INVENTARIO & DECK RETRAIBILE */
    .inv-row-container { text-align: left !important; width: 100%; padding-left: 10px; }
    .inv-row button {
        width: 100% !important; justify-content: flex-start !important; background: transparent !important;
        border: none !important; color: #f1f5f9 !important; text-align: left !important; font-size: 1.1rem !important;
    }
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; text-align: left !important; margin-bottom: 5px !important; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# FUNZIONI UTILI
# =========================
@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame(), {}
    df = pd.read_csv("beyblade_x.csv").fillna("")
    
    # Creiamo una mappa globale Nome -> Immagine per il Builder
    img_map = {}
    mapping_rules = [
        ('lock_chip', 'lock_chip_image'), ('blade', 'blade_image'),
        ('main_blade', 'main_blade_image'), ('assist_blade', 'assist_blade_image'),
        ('ratchet', 'ratchet_image'), ('bit', 'bit_image'),
        ('ratchet_integrated_bit', 'ratchet_integrated_bit_image')
    ]
    for comp_col, img_col in mapping_rules:
        if comp_col in df.columns and img_col in df.columns:
            for _, r in df.iterrows():
                nome, url = r[comp_col], r[img_col]
                if nome and nome != "n/a" and url and url != "n/a":
                    img_map[nome] = url
    
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df, img_map

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
            if nome in st.session_state.inventario[tipo]:
                del st.session_state.inventario[tipo][nome]

# Inizializzazione Stati
if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}
if 'deck_name' not in st.session_state: st.session_state.deck_name = "IL MIO DECK"
if 'editing_name' not in st.session_state: st.session_state.editing_name = False
if 'deck_selections' not in st.session_state: st.session_state.deck_selections = {i: {} for i in range(3)}

df, global_img_map = load_db()

# =========================
# UI PRINCIPALE
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

# --- TAB 1: AGGIUNGI (INTOCCABILE) ---
with tab1:
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
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                for ck, ik in components:
                    if row[ck] and row[ck] != "n/a": add_to_inv(ik, row[ck])
                st.toast("Set aggiunto!")
            st.markdown("<hr>", unsafe_allow_html=True)
            for ck, ik in components:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name-centered'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        add_to_inv(ik, val)
                        st.toast(f"Aggiunto: {val}")

# --- TAB 2: INVENTARIO (INTOCCABILE) ---
with tab2:
    modo = st.radio("L", ["Aggiungi (+1)", "Rimuovi (-1)"], horizontal=True, label_visibility="collapsed")
    operazione = 1 if "Aggiungi" in modo else -1
    has_content = any(len(v) > 0 for v in st.session_state.inventario.values())
    if not has_content:
        st.info("L'inventario è vuoto.")
    else:
        for categoria, pezzi in st.session_state.inventario.items():
            if pezzi:
                cat_label = categoria.replace('_', ' ').upper()
                with st.expander(cat_label, expanded=False):
                    st.markdown('<div class="inv-row-container">', unsafe_allow_html=True)
                    for nome, qta in pezzi.items():
                        if st.button(f"{nome} x{qta}", key=f"inv_{categoria}_{nome}"):
                            add_to_inv(categoria, nome, operazione); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: DECK BUILDER (RIPRISTINATO) ---
with tab3:
    with st.expander(f"{st.session_state.deck_name.upper()}", expanded=True):
        
        def get_options(cat, theory=False):
            if theory:
                csv_map = {"lock_bit": "lock_chip", "blade": "blade", "main_blade": "main_blade",
                           "assist_blade": "assist_blade", "ratchet": "ratchet", "bit": "bit",
                           "ratchet_integrated_bit": "ratchet_integrated_bit"}
                col_name = csv_map.get(cat, cat)
                opts = df[col_name].unique().tolist()
                return ["-"] + sorted([x for x in opts if x and x != "n/a"])
            return ["-"] + sorted(list(st.session_state.inventario[cat].keys()))

        tipologie = ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", "BX/UX Theory", "CX Theory", "BX/UX+RIB Theory", "CX+RIB Theory"]

        for idx in range(3):
            sels = st.session_state.deck_selections[idx]
            nome_parti = [v for v in sels.values() if v and v != "-"]
            titolo_slot = " ".join(nome_parti) if nome_parti else f"SLOT {idx+1}"
            
            with st.expander(titolo_slot.upper(), expanded=False):
                tipo = st.selectbox("Sistema", tipologie, key=f"type_{idx}")
                is_theory = "Theory" in tipo
                current_sels = {}

                # Logica Selezione componenti
                if "BX/UX" in tipo and "+RIB" not in tipo:
                    current_sels['b'] = st.selectbox("Blade", get_options("blade", is_theory), key=f"b_{idx}")
                    current_sels['r'] = st.selectbox("Ratchet", get_options("ratchet", is_theory), key=f"r_{idx}")
                    current_sels['bi'] = st.selectbox("Bit", get_options("bit", is_theory), key=f"bi_{idx}")
                elif "CX" in tipo and "+RIB" not in tipo:
                    current_sels['lb'] = st.selectbox("Lock Bit", get_options("lock_bit", is_theory), key=f"lb_{idx}")
                    current_sels['mb'] = st.selectbox("Main Blade", get_options("main_blade", is_theory), key=f"mb_{idx}")
                    current_sels['ab'] = st.selectbox("Assist Blade", get_options("assist_blade", is_theory), key=f"ab_{idx}")
                    current_sels['r'] = st.selectbox("Ratchet", get_options("ratchet", is_theory), key=f"r_{idx}")
                    current_sels['bi'] = st.selectbox("Bit", get_options("bit", is_theory), key=f"bi_{idx}")
                elif "BX/UX+RIB" in tipo:
                    current_sels['b'] = st.selectbox("Blade", get_options("blade", is_theory), key=f"b_{idx}")
                    current_sels['rib'] = st.selectbox("RIB", get_options("ratchet_integrated_bit", is_theory), key=f"rib_{idx}")
                elif "CX+RIB" in tipo:
                    current_sels['lb'] = st.selectbox("Lock Bit", get_options("lock_bit", is_theory), key=f"lb_{idx}")
                    current_sels['mb'] = st.selectbox("Main Blade", get_options("main_blade", is_theory), key=f"mb_{idx}")
                    current_sels['ab'] = st.selectbox("Assist Blade", get_options("assist_blade", is_theory), key=f"ab_{idx}")
                    current_sels['rib'] = st.selectbox("RIB", get_options("ratchet_integrated_bit", is_theory), key=f"rib_{idx}")

                # Visualizzazione Immagini Componenti
                st.write("")
                img_cols = st.columns(len(current_sels) if current_sels else 1)
                for i, (k, v) in enumerate(current_sels.items()):
                    if v != "-":
                        url = global_img_map.get(v)
                        if url:
                            img_obj = get_img(url)
                            if img_obj: img_cols[i].image(img_obj, caption=v, use_container_width=True)

                if st.session_state.deck_selections[idx] != current_sels:
                    st.session_state.deck_selections[idx] = current_sels
                    st.rerun()

        # Modifica Nome Deck
        st.markdown("<br>", unsafe_allow_html=True)
        if not st.session_state.editing_name:
            if st.button("📝 Modifica Nome Deck"):
                st.session_state.editing_name = True; st.rerun()
        else:
            new_name = st.text_input("Nuovo nome:", st.session_state.deck_name)
            c1, c2 = st.columns([0.2, 1])
            if c1.button("Salva"):
                st.session_state.deck_name = new_name
                st.session_state.editing_name = False; st.rerun()
            if c2.button("Annulla"):
                st.session_state.editing_name = False; st.rerun()