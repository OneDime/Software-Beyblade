import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & FIX CENTRATURA MOBILE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo Generale */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* INTESTAZIONI SCURE (Bloccate) */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }
    div[data-testid="stExpander"] summary { background-color: #1e293b !important; border-radius: 10px; }
    div[data-testid="stExpander"] summary p { color: #cbd5e1 !important; font-weight: bold; }

    /* CENTRATURA CARD E CONTENUTO */
    [data-testid="stVerticalBlock"] > div {
        text-align: center;
    }

    /* FIX DEFINITIVO COLONNE: Forza l'affiancamento anche su smartphone */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important; /* Forza la riga */
        flex-wrap: nowrap !important;   /* Impedisce di andare a capo */
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
    }

    /* Proporzioni colonne bloccate */
    [data-testid="column"] {
        width: auto !important;
        flex: 1 1 auto !important;
        min-width: 0px !important;
    }

    /* Stile Bottoni */
    button {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
        border: 1px solid #475569 !important;
        height: 38px !important;
    }
    
    /* Centratura specifica per i testi dei componenti */
    .component-text {
        text-align: left;
        font-size: 1rem;
        padding-left: 10px;
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
def get_img(url, size=(200, 200)):
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

df = load_db()

# =========================
# UI PRINCIPALE
# =========================
tab_add, tab_inv, tab_deck = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab_add:
    search_q = st.text_input("Cerca...", key="search_main")
    filtered = df[df['_search'].str.contains(search_q.lower())].head(3) if len(search_q) >= 2 else df.head(3)

    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            # Titolo centrato
            st.markdown(f"<h3 style='color:#60a5fa;'>{row['name'].upper()}</h3>", unsafe_allow_html=True)
            
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img: st.image(img, width=200)
            
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Usiamo colonne fisiche di Streamlit, ma il CSS sopra le terrà affiancate
                    c_txt, c_btn = st.columns([0.7, 0.3])
                    c_txt.markdown(f"<div class='component-text'>{val}</div>", unsafe_allow_html=True)
                    if c_btn.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            st.write("") # Spazio
            if st.button("Aggiungi tutto", key=f"all_{i}", use_container_width=True):
                for field, inv_key in comps:
                    val = row[field]
                    if val and val != "n/a":
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                st.toast(f"Aggiunti tutti i componenti di {row['name']}")

with tab_inv:
    st.header(f"Inventario")
    for tipo in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]:
        pezzi = st.session_state.inventario.get(tipo, {})
        validi = {k: v for k, v in pezzi.items() if v > 0}
        if validi:
            with st.expander(tipo.replace('_', ' ').upper(), expanded=True):
                for nome, qta in validi.items():
                    # Anche qui forziamo l'affiancamento
                    ci1, ci2, ci3 = st.columns([0.5, 0.25, 0.25])
                    ci1.markdown(f"<div style='text-align:left;'>{nome} (x{qta})</div>", unsafe_allow_html=True)
                    if ci2.button("＋", key=f"inv_p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if ci3.button("－", key=f"inv_m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()