import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE CSS AVANZATO
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo e Testi Generali */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* Forza centratura del titolo e dell'immagine */
    .centered-title { text-align: center; color: #60a5fa; font-weight: bold; margin-bottom: 10px; }
    
    /* FIX TESTI TAB E LABEL: Grigio chiarissimo */
    .stTabs [data-baseweb="tab-list"] button p, label p, .stMarkdown p {
        color: #f1f5f9 !important;
    }

    /* FIX EXPANDER (Intestazioni Inventario e Deck) */
    .streamlit-expanderHeader {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 8px !important;
    }
    .streamlit-expanderHeader p { color: #f1f5f9 !important; font-weight: bold; }

    /* BOTTONI: Scuri con bordo blu */
    button, [data-testid="stBaseButton-secondary"] {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 1px solid #3b82f6 !important;
    }

    /* CONTENITORE RIGA COMPONENTE (Per Aggiungi e Inventario) */
    .custom-row {
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: center;
        gap: 15px;
        width: 100%;
        margin: 8px 0;
    }

    .comp-text {
        color: #e2e8f0;
        font-size: 1rem;
        min-width: 120px;
        text-align: right;
    }

    /* Centratura immagini */
    [data-testid="stImage"] img {
        margin: 0 auto !important;
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
            st.markdown(f"<h3 class='centered-title'>{row['name'].upper()}</h3>", unsafe_allow_html=True)
            
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                st.image(img, width=180)
            
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Usiamo una riga "mista" per mantenere l'allineamento
                    c_txt, c_btn = st.columns([0.7, 0.3])
                    with c_txt:
                        st.markdown(f"<div style='text-align: right; padding-top: 5px; color: #f1f5f9;'>{val}</div>", unsafe_allow_html=True)
                    with c_btn:
                        if st.button("＋", key=f"add_{i}_{field}"):
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
    for tipo in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]:
        pezzi = st.session_state.inventario.get(tipo, {})
        validi = {k: v for k, v in pezzi.items() if v > 0}
        
        if validi:
            with st.expander(tipo.replace('_', ' ').upper(), expanded=True):
                for nome, qta in validi.items():
                    # Forza tutto sulla stessa riga con Flexbox HTML
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; background: #0f172a; padding: 10px; border-radius: 8px;">
                        <div style="color: #f1f5f9;">{nome} (x{qta})</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c_p, c_m = st.columns(2)
                    if c_p.button("＋", key=f"p_{tipo}_{nome}", use_container_width=True):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if c_m.button("－", key=f"m_{tipo}_{nome}", use_container_width=True):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()

with tab_deck:
    st.header(f"Deck Builder")
    if st.button("➕ Nuovo Deck", use_container_width=True):
        st.session_state.decks.append({"name": f"Deck {len(st.session_state.decks)+1}"})

    for d_idx, deck in enumerate(st.session_state.decks):
        with st.expander(f"📂 {deck['name']}", expanded=True):
            for b_idx in range(3):
                st.markdown(f"<div style='text-align: center; font-weight: bold; margin-top: 10px;'>BEYBLADE {b_idx+1}</div>", unsafe_allow_html=True)
                
                # Flag
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
                    if v_th: 
                        opts = [""] + sorted(df[db_key].unique().tolist())
                    else:
                        inv_k = "lock_bit" if db_key == "lock_chip" else db_key
                        inv_data = st.session_state.inventario.get(inv_k, {})
                        opts = [""] + sorted([k for k, v in inv_data.items() if v > 0])
                    
                    # Centratura selettore + immagine
                    scelta = st.selectbox(label, opts, key=f"dk_{d_idx}_{b_idx}_{db_key}")
                    if scelta:
                        img_url = df[df[db_key] == scelta][img_db_key].values
                        if len(img_url) > 0:
                            p_img = get_img(img_url[0], size=(100, 100))
                            if p_img: st.image(p_img, width=100)