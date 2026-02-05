import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE DEFINITIVO
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo e Testi Generali */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* Forza centratura di TUTTI i blocchi nel container */
    [data-testid="stVerticalBlock"] {
        align-items: center !important;
        text-align: center !important;
    }

    /* Testi Tab e Label chiari */
    .stTabs [data-baseweb="tab-list"] button p, label p, .stMarkdown p {
        color: #f1f5f9 !important;
    }

    /* BOTTONI: Scuri su ogni dispositivo */
    button, [data-testid="stBaseButton-secondary"] {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 1px solid #3b82f6 !important;
    }

    /* RIGA COMPONENTE: Flexbox per tenere tutto sulla stessa linea */
    .comp-container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin: 5px 0;
    }
    
    /* Impedisce ai bottoni di Streamlit di forzare il wrap su mobile */
    [data-testid="column"] {
        width: fit-content !important;
        flex: unset !important;
        min-width: unset !important;
    }

    /* Centratura immagini */
    [data-testid="stImage"] img {
        margin-left: auto;
        margin-right: auto;
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# FUNZIONI CORE
# =========================
@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame()
    df = pd.read_csv("beyblade_x.csv").fillna("")
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df

@st.cache_resource
def get_img(url, size=(180, 180)):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join("images", f"{h}.png")
    if os.path.exists(path):
        img = Image.open(path)
        img.thumbnail(size)
        return img
    return None

if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}
if 'decks' not in st.session_state:
    st.session_state.decks = []

df = load_db()
st.sidebar.title("🔧 Officina X")
utente = st.sidebar.selectbox("Utente", ["Antonio", "Andrea", "Fabio"])

# =========================
# TABS
# =========================
tab_add, tab_inv, tab_deck = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab_add:
    search_q = st.text_input("Cerca...", key="search_bar")
    
    filtered = df
    if len(search_q) >= 2:
        filtered = df[df['_search'].str.contains(search_q.lower())]
    else:
        filtered = df.head(3)

    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            # Centratura Titolo e Immagine
            st.markdown(f"### {row['name'].upper()}")
            
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                st.image(img, width=180)
            
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Layout super-stretto per forzare l'affiancamento
                    c1, c2 = st.columns([0.85, 0.15])
                    c1.markdown(f"<div style='text-align: right; padding-top: 5px;'>{val}</div>", unsafe_allow_html=True)
                    if c2.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            st.write("")
            if st.button("Aggiungi tutto", key=f"all_{i}", use_container_width=True):
                for f, k in comps:
                    if row[f] and row[f] != "n/a":
                        st.session_state.inventario[k][row[f]] = st.session_state.inventario[k].get(row[f], 0) + 1
                st.toast("Beyblade aggiunto!")

with tab_inv:
    st.header(f"Inventario di {utente}")
    # Fix Logica Inventario per evitare IndexError
    for tipo in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]:
        pezzi = st.session_state.inventario.get(tipo, {})
        validi = {k: v for k, v in pezzi.items() if v > 0}
        
        if validi:
            with st.expander(tipo.replace('_', ' ').upper(), expanded=True):
                for nome, qta in validi.items():
                    c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                    c1.write(f"{nome} (x{qta})")
                    if c2.button("＋", key=f"p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if c3.button("－", key=f"m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()

with tab_deck:
    st.header(f"Deck Builder")
    if st.button("➕ Nuovo Deck", use_container_width=True):
        st.session_state.decks.append({"name": f"Deck {len(st.session_state.decks)+1}"})

    for d_idx, deck in enumerate(st.session_state.decks):
        with st.expander(f"📂 {deck['name']}", expanded=True):
            for b_idx in range(3):
                st.markdown(f"**BEYBLADE {b_idx+1}**")
                f1, f2, f3 = st.columns(3)
                v_cx = f1.checkbox("CX", key=f"cx_{d_idx}_{b_idx}")
                v_rib = f2.checkbox("RIB", key=f"rib_{d_idx}_{b_idx}")
                v_th = f3.checkbox("Theory", key=f"th_{d_idx}_{b_idx}")
                
                parts = []
                if v_cx: parts += [("Lock Bit", "lock_chip", "lock_chip_image"), ("Main Blade", "main_blade", "main_blade_image"), ("Assist Blade", "assist_blade", "assist_blade_image")]
                else: parts += [("Blade", "blade", "blade_image")]
                if v_rib: parts += [("R.I.B.", "ratchet_integrated_bit", "ratchet_integrated_bit_image")]
                else: parts += [("Ratchet", "ratchet", "ratchet_image"), ("Bit", "bit", "bit_image")]

                for label, db_key, img_db_key in parts:
                    # Fix logica opzioni: correzione IndexError
                    if v_th: 
                        opts = [""] + sorted(df[db_key].unique().tolist())
                    else:
                        inv_k = "lock_bit" if db_key == "lock_chip" else db_key
                        inv_data = st.session_state.inventario.get(inv_k, {})
                        opts = [""] + sorted([k for k, v in inv_data.items() if v > 0])
                    
                    c_sel, c_img = st.columns([0.75, 0.25])
                    scelta = c_sel.selectbox(label, opts, key=f"dk_{d_idx}_{b_idx}_{db_key}")
                    if scelta:
                        img_url = df[df[db_key] == scelta][img_db_key].values
                        if len(img_url) > 0:
                            p_img = get_img(img_url[0], size=(80, 80))
                            if p_img: c_img.image(p_img)