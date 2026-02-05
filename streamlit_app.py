import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE (INVARIATI)
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* STILE TAB AGGIUNGI (INTOCCABILE) */
    [data-testid="stVerticalBlock"] { text-align: center; align-items: center; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 25px !important;
        padding: 15px !important;
    }
    .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; margin-bottom: 8px; text-align: center; }
    .comp-name-centered { font-size: 1.1rem; color: #cbd5e1; margin-top: 5px; margin-bottom: 2px; text-align: center; width: 100%; display: block; }

    /* BOTTONI AGGIUNGI (INTOCCABILI) */
    div.stButton > button {
        width: auto !important; min-width: 150px !important; padding-left: 40px !important; padding-right: 40px !important;
        height: 30px !important; background-color: #334155 !important; color: white !important;
        border: 1px solid #475569 !important; border-radius: 4px !important; font-size: 1.1rem !important;
    }

    /* STILE INVENTARIO */
    .inv-row-container { text-align: left !important; width: 100%; padding-left: 10px; }
    .inv-row button {
        width: 100% !important; justify-content: flex-start !important; background: transparent !important;
        border: none !important; color: #f1f5f9 !important; text-align: left !important; font-size: 1.1rem !important;
    }

    /* STILE DECK BUILDER */
    .deck-slot {
        background-color: #1e293b;
        border: 1px dashed #60a5fa;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 20px;
    }
    .deck-title { color: #60a5fa; font-weight: bold; margin-bottom: 10px; font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# FUNZIONI UTILI (INVARIATE)
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

# Inizializzazione Inventario e Deck
if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}

if 'deck' not in st.session_state:
    st.session_state.deck = {
        "Bey 1": {"blade": None, "ratchet": None, "bit": None},
        "Bey 2": {"blade": None, "ratchet": None, "bit": None},
        "Bey 3": {"blade": None, "ratchet": None, "bit": None},
    }

df = load_db()

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

# --- TAB 2: INVENTARIO (INTOCCABILE) ---
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
                        st.markdown('<div class="inv-row">', unsafe_allow_html=True)
                        if st.button(f"{nome} x{qta}", key=f"inv_{categoria}_{nome}"):
                            add_to_inv(categoria, nome, operazione)
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: DECK BUILDER ---
with tab3:
    st.markdown("<div class='bey-name'>Il Tuo Deck (3 Slot)</div>", unsafe_allow_html=True)
    
    # Prepariamo le liste per i selectbox basate sull'inventario
    # Uniamo le varie tipologie di blade e ratchet per semplicità
    available_blades = ["Seleziona..."] + sorted(list(st.session_state.inventario["blade"].keys()) + list(st.session_state.inventario["main_blade"].keys()))
    available_ratchets = ["Seleziona..."] + sorted(list(st.session_state.inventario["ratchet"].keys()))
    available_bits = ["Seleziona..."] + sorted(list(st.session_state.inventario["bit"].keys()))

    cols = st.columns(3)
    
    for idx, (bey_label, bey_data) in enumerate(st.session_state.deck.items()):
        with cols[idx]:
            with st.container(border=True):
                st.markdown(f"<div class='deck-title'>{bey_label}</div>", unsafe_allow_html=True)
                
                # Selezione componenti
                # Nota: Streamlit non permette duplicati nelle chiavi dei pezzi, usiamo indici
                st.session_state.deck[bey_label]["blade"] = st.selectbox(f"Blade", available_blades, key=f"sel_b_{idx}")
                st.session_state.deck[bey_label]["ratchet"] = st.selectbox(f"Ratchet", available_ratchets, key=f"sel_r_{idx}")
                st.session_state.deck[bey_label]["bit"] = st.selectbox(f"Bit", available_bits, key=f"sel_bit_{idx}")
                
                # Visualizzazione anteprima (se selezionato)
                if st.session_state.deck[bey_label]["blade"] != "Seleziona...":
                    # Cerchiamo l'immagine della blade nel CSV
                    blade_name = st.session_state.deck[bey_label]["blade"]
                    img_url = df[df['blade'] == blade_name]['blade_image'].values
                    if len(img_url) > 0 and img_url[0] != "n/a":
                        img = get_img(img_url[0])
                        if img: st.image(img, use_container_width=True)