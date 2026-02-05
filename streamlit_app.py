import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE "LOCK-LAYOUT"
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* FIX INTESTAZIONI: Finalmente scure */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }
    div[data-testid="stExpander"] summary { background-color: #1e293b !important; }
    div[data-testid="stExpander"] summary p { color: #cbd5e1 !important; font-weight: bold; }

    /* CENTRATURA TITOLO E IMMAGINE */
    .centered-text { text-align: center; width: 100%; display: block; }
    [data-testid="stImage"] { display: flex; justify-content: center; }
    [data-testid="stImage"] img { margin: 0 auto !important; }

    /* FORZA RIGA ORIZZONTALE (Il segreto è il Flexbox applicato al blocco orizzontale) */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important; /* Forza orizzontale anche su mobile */
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
    }

    /* Regola le colonne interne per non collassare */
    div[data-testid="column"] {
        width: auto !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* Bottone piccolissimo per il "+" */
    .stButton button {
        width: 45px !important;
        height: 45px !important;
        padding: 0 !important;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-left: auto !important; /* Spinge il tasto a destra */
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
def get_img(url, size=(220, 220)):
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
utente = st.sidebar.selectbox("Utente", ["Antonio", "Andrea", "Fabio"])

# =========================
# TABS
# =========================
tab_add, tab_inv, tab_deck = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab_add:
    search_q = st.text_input("Cerca...")
    
    filtered = df[df['_search'].str.contains(search_q.lower())].head(3) if len(search_q) >= 2 else df.head(3)

    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            # 1. NOME (Centrato)
            st.markdown(f"<h2 class='centered-text' style='color:#60a5fa;'>{row['name'].upper()}</h2>", unsafe_allow_html=True)
            
            # 2. IMMAGINE (Centrata)
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                st.image(img)
            
            # 3. COMPONENTI (Testo a sinistra, Tasto a destra)
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Usiamo colonne ma il CSS 'flex-direction: row' impedisce che vadano a capo
                    c_txt, c_btn = st.columns([0.8, 0.2])
                    c_txt.markdown(f"<div style='padding-top:10px; font-size:1.1rem;'>{val}</div>", unsafe_allow_html=True)
                    if c_btn.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            # 4. AGGIUNGI TUTTO (Centrato sotto)
            st.write("")
            if st.button("Aggiungi tutto", key=f"btn_all_{i}", use_container_width=True):
                for f, k in comps:
                    if row[f] and row[f] != "n/a":
                        st.session_state.inventario[k][row[f]] = st.session_state.inventario[k].get(row[f], 0) + 1
                st.toast("Beyblade aggiunto!")

with tab_inv:
    st.header(f"Inventario")
    for tipo in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]:
        pezzi = st.session_state.inventario.get(tipo, {})
        validi = {k: v for k, v in pezzi.items() if v > 0}
        
        if validi:
            with st.expander(tipo.replace('_', ' ').upper(), expanded=True):
                for nome, qta in validi.items():
                    # Layout: Nome | + | -
                    c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                    c1.markdown(f"<div style='padding-top:10px;'>{nome} (x{qta})</div>", unsafe_allow_html=True)
                    if c2.button("＋", key=f"inv_p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if c3.button("－", key=f"inv_m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()