import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & FIX DEFINITIVI
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo Generale */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* FIX INTESTAZIONI: Finalmente scure come richiesto */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
    }
    /* Colore testo e sfondo della barra dell'expander */
    div[data-testid="stExpander"] summary {
        background-color: #1e293b !important;
        color: #cbd5e1 !important;
    }
    /* Forza il colore del testo dentro l'intestazione */
    div[data-testid="stExpander"] summary p {
        color: #cbd5e1 !important;
    }

    /* CENTRATURA E DIMENSIONE IMMAGINE */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }
    [data-testid="stImage"] img {
        width: 150px !important; /* Dimensione controllata */
        height: auto;
    }

    /* CENTRATURA TITOLO */
    .centered-title {
        text-align: center;
        width: 100%;
        color: #60a5fa;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    /* BOTTONI STANDARD */
    button {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
        border: 1px solid #475569 !important;
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
def get_img(url, size=(150, 150)):
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
            # 1. Nome Beyblade Centrato
            st.markdown(f"<h3 class='centered-title'>{row['name']}</h3>", unsafe_allow_html=True)
            
            # 2. Immagine Beyblade Centrata e Piccola
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                st.image(img)
            
            st.write("") # Spazio minimo
            
            # 3. Componenti con tasto accanto
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Layout: Testo a sinistra (85%), Tasto a destra (15%)
                    c_txt, c_btn = st.columns([0.85, 0.15])
                    c_txt.write(val)
                    if c_btn.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            # 4. Aggiungi tutto (Piena larghezza)
            if st.button("Aggiungi tutto", key=f"all_btn_{i}", use_container_width=True):
                for f, k in comps:
                    if row[f] and row[f] != "n/a":
                        st.session_state.inventario[k][row[f]] = st.session_state.inventario[k].get(row[f], 0) + 1
                st.toast("Set aggiunto")

with tab_inv:
    st.header("Inventario")
    for tipo in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]:
        pezzi = st.session_state.inventario.get(tipo, {})
        validi = {k: v for k, v in pezzi.items() if v > 0}
        if validi:
            # Intestazione scura forzata via CSS sopra
            with st.expander(tipo.replace('_', ' ').upper(), expanded=True):
                for nome, qta in validi.items():
                    ci1, ci2, ci3 = st.columns([0.6, 0.2, 0.2])
                    ci1.write(f"{nome} (x{qta})")
                    if ci2.button("＋", key=f"inv_p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if ci3.button("－", key=f"inv_m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()