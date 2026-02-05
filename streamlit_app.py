import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & FIX MOBILE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo e Colori Base */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* Expander: Sfondo scuro e scritte chiare */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
    }
    div[data-testid="stExpander"] summary p { color: #cbd5e1 !important; }

    /* Centratura Immagini */
    [data-testid="stImage"] img { display: block; margin: 0 auto; }

    /* FIX LAYOUT: Impedisce ai tasti di uscire o essere tagliati */
    [data-testid="column"] {
        display: flex !important;
        align-items: center !important;
    }
    
    /* Blocca la colonna del tasto a una dimensione fissa e sicura */
    div[data-testid="column"]:nth-of-type(2), 
    div[data-testid="column"]:nth-of-type(3) {
        min-width: 50px !important;
        max-width: 50px !important;
        justify-content: center !important;
    }

    /* Tasti standard scuri */
    .stButton button {
        background-color: #334155 !important;
        color: white !important;
        border: 1px solid #475569 !important;
        width: 40px !important;
        height: 35px !important;
        padding: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# FUNZIONI CORE
# =========================
@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): 
        return pd.DataFrame(columns=['name', 'blade_image', 'beyblade_page_image', 'lock_chip', 'blade', 'main_blade', 'assist_blade', 'ratchet', 'bit', 'ratchet_integrated_bit', '_search'])
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

# Inizializzazione dati
if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}
if 'decks' not in st.session_state:
    st.session_state.decks = []

df = load_db()

# =========================
# UI PRINCIPALE
# =========================
tab_add, tab_inv, tab_deck = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab_add:
    search_q = st.text_input("Cerca...", key="search_main")
    # Qui il fix per il NameError: df è definito sopra
    filtered = df[df['_search'].str.contains(search_q.lower())].head(3) if len(search_q) >= 2 else df.head(3)

    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.markdown(f"<h3 style='text-align:center; color:#60a5fa;'>{row['name'].upper()}</h3>", unsafe_allow_html=True)
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img: st.image(img, width=180)
            
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Layout super-stabile: il testo occupa l'80%, il tasto il 20% fisso
                    c_txt, c_btn = st.columns([0.8, 0.2])
                    c_txt.write(val)
                    if c_btn.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            st.button("Aggiungi tutto", key=f"all_{i}", use_container_width=True)

with tab_inv:
    st.header("Inventario")
    for tipo in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]:
        pezzi = st.session_state.inventario.get(tipo, {})
        validi = {k: v for k, v in pezzi.items() if v > 0}
        if validi:
            with st.expander(tipo.replace('_', ' ').upper(), expanded=True):
                for nome, qta in validi.items():
                    # Qui usiamo 3 colonne: Nome | + | -
                    ci1, ci2, ci3 = st.columns([0.6, 0.2, 0.2])
                    ci1.write(f"{nome} (x{qta})")
                    if ci2.button("＋", key=f"inv_p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if ci3.button("－", key=f"inv_m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()

# Il Deck Builder rimane come lo avevi lasciato, ma ora eredita lo stile scuro degli expander.