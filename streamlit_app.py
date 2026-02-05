import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & FIX RADICALE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

# CSS mirato solo a quello che hai chiesto: centratura e intestazioni scure
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* FIX INTESTAZIONI: Devono essere scure */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
    }
    div[data-testid="stExpander"] summary { background-color: #1e293b !important; }
    div[data-testid="stExpander"] summary p { color: #f1f5f9 !important; }

    /* CENTRATURA IMMAGINE */
    [data-testid="stImage"] { display: flex; justify-content: center; width: 100%; }
    [data-testid="stImage"] img { margin: 0 auto !important; }

    /* TABELLA COMPONENTI: Forza l'allineamento orizzontale */
    .comp-table {
        width: 100%;
        border-collapse: collapse;
    }
    .comp-table td {
        vertical-align: middle;
        padding: 5px 0;
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
if 'decks' not in st.session_state:
    st.session_state.decks = []

df = load_db()

# =========================
# TABS
# =========================
tab_add, tab_inv, tab_deck = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab_add:
    search_q = st.text_input("Cerca...", key="search_main")
    filtered = df[df['_search'].str.contains(search_q.lower())].head(3) if len(search_q) >= 2 else df.head(3)

    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.markdown(f"<h3 style='text-align:center;'>{row['name'].upper()}</h3>", unsafe_allow_html=True)
            
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                st.image(img)
            
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            # USIAMO LE COLONNE MA CON LOGICA DIVERSA PER EVITARE SPOSTAMENTI
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Layout super-protetto: colonna larghissima per il testo, strettissima per il tasto
                    c1, c2 = st.columns([0.85, 0.15])
                    c1.write(val)
                    if c2.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            st.button("Aggiungi tutto", key=f"all_{i}", use_container_width=True)

with tab_inv:
    st.header(f"Inventario")
    for tipo in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]:
        pezzi = st.session_state.inventario.get(tipo, {})
        validi = {k: v for k, v in pezzi.items() if v > 0}
        
        if validi:
            with st.expander(tipo.replace('_', ' ').upper(), expanded=True):
                for nome, qta in validi.items():
                    # Qui mettiamo 3 colonne: Nome, +, -
                    ci1, ci2, ci3 = st.columns([0.7, 0.15, 0.15])
                    ci1.write(f"{nome} (x{qta})")
                    if ci2.button("＋", key=f"inv_p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if ci3.button("－", key=f"inv_m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()