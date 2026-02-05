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
    
    /* --- TAB AGGIUNGI (INTOCCABILE) --- */
    .add-container [data-testid="stVerticalBlock"] { text-align: center; align-items: center; }
    .add-container div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 25px !important;
        padding: 15px !important;
    }
    .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; margin-bottom: 8px; text-align: center; }
    .comp-name-centered { font-size: 1.1rem; color: #cbd5e1; margin-top: 5px; margin-bottom: 2px; text-align: center; width: 100%; display: block; }
    div.stButton > button {
        width: auto !important; min-width: 150px !important; padding-left: 40px !important; padding-right: 40px !important;
        height: 30px !important; background-color: #334155 !important; color: white !important;
        border: 1px solid #475569 !important; border-radius: 4px !important; font-size: 1.1rem !important;
    }

    /* --- TAB INVENTARIO (ALLINEAMENTO A SINISTRA) --- */
    [data-testid="stExpander"] [data-testid="stVerticalBlock"] {
        text-align: left !important;
        align-items: flex-start !important;
    }
    .inv-row-container { 
        text-align: left !important; 
        width: 100%; 
        display: flex;
        flex-direction: column;
        align-items: flex-start !important;
    }
    .inv-row-container button {
        width: 100% !important; 
        justify-content: flex-start !important; 
        background: transparent !important;
        border: none !important; 
        color: #f1f5f9 !important; 
        text-align: left !important; 
        font-size: 1.1rem !important;
        padding-left: 5px !important;
    }
    
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
            if nome in st.session_state.inventario[tipo]:
                del st.session_state.inventario[tipo][nome]

if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}

if 'deck_name' not in st.session_state:
    st.session_state.deck_name = "IL MIO DECK"

if 'editing_name' not in st.session_state:
    st.session_state.editing_name = False

df = load_db()

# =========================
# UI PRINCIPALE
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

# --- TAB 1: AGGIUNGI (INTOCCABILE) ---
with tab1:
    st.markdown('<div class="add-container">', unsafe_allow_html=True)
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

# --- TAB 2: INVENTARIO (SINISTRA) ---
with tab2:
    modo = st.radio("Label_Hidden", ["Aggiungi (+1)", "Rimuovi (-1)"], horizontal=True, label_visibility="collapsed")
    operazione = 1 if "Aggiungi" in modo else -1
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
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
                            add_to_inv(categoria, nome, operazione)
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: DECK BUILDER ---
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
            else:
                return ["-"] + sorted(list(st.session_state.inventario[cat].keys()))

        tipologie = ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", 
                     "BX/UX Theory", "CX Theory", "BX/UX+RIB Theory", "CX+RIB Theory"]

        for idx in range(3):
            # Costruzione titolo dinamico SENZA rerun forzato
            # Recuperiamo i valori direttamente dai widget usando i key
            b = st.session_state.get(f"b_{idx}", "-")
            r = st.session_state.get(f"r_{idx}", "-")
            bi = st.session_state.get(f"bi_{idx}", "-")
            lb = st.session_state.get(f"lb_{idx}", "-")
            mb = st.session_state.get(f"mb_{idx}", "-")
            ab = st.session_state.get(f"ab_{idx}", "-")
            rib = st.session_state.get(f"rib_{idx}", "-")

            # Logica di composizione nome in base al sistema (senza i "-")
            parti = [p for p in [lb, mb, ab, b, r, bi, rib] if p and p != "-"]
            titolo_slot = " ".join(parti) if parti else f"SLOT {idx+1}"
            
            with st.expander(titolo_slot.upper(), expanded=False):
                tipo = st.selectbox("Sistema", tipologie, key=f"type_{idx}")
                is_theory = "Theory" in tipo
                
                if "BX/UX" in tipo and "+RIB" not in tipo:
                    st.selectbox("Blade", get_options("blade", is_theory), key=f"b_{idx}")
                    st.selectbox("Ratchet", get_options("ratchet", is_theory), key=f"r_{idx}")
                    st.selectbox("Bit", get_options("bit", is_theory), key=f"bi_{idx}")
                elif "CX" in tipo and "+RIB" not in tipo:
                    st.selectbox("Lock Bit", get_options("lock_bit", is_theory), key=f"lb_{idx}")
                    st.selectbox("Main Blade", get_options("main_blade", is_theory), key=f"mb_{idx}")
                    st.selectbox("Assist Blade", get_options("assist_blade", is_theory), key=f"ab_{idx}")
                    st.selectbox("Ratchet", get_options("ratchet", is_theory), key=f"r_{idx}")
                    st.selectbox("Bit", get_options("bit", is_theory), key=f"bi_{idx}")
                elif "BX/UX+RIB" in tipo:
                    st.selectbox("Blade", get_options("blade", is_theory), key=f"b_{idx}")
                    st.selectbox("RIB", get_options("ratchet_integrated_bit", is_theory), key=f"rib_{idx}")
                elif "CX+RIB" in tipo:
                    st.selectbox("Lock Bit", get_options("lock_bit", is_theory), key=f"lb_{idx}")
                    st.selectbox("Main Blade", get_options("main_blade", is_theory), key=f"mb_{idx}")
                    st.selectbox("Assist Blade", get_options("assist_blade", is_theory), key=f"ab_{idx}")
                    st.selectbox("RIB", get_options("ratchet_integrated_bit", is_theory), key=f"rib_{idx}")

        st.markdown("<br>", unsafe_allow_html=True)
        if not st.session_state.editing_name:
            if st.button("📝 Modifica Nome Deck"):
                st.session_state.editing_name = True
                st.rerun()
        else:
            new_name = st.text_input("Nuovo nome:", st.session_state.deck_name)
            col_save, col_cancel = st.columns([1, 1])
            with col_save:
                if st.button("Salva"):
                    st.session_state.deck_name = new_name
                    st.session_state.editing_name = False
                    st.rerun()
            with col_cancel:
                if st.button("Annulla"):
                    st.session_state.editing_name = False
                    st.rerun()