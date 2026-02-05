import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & CSS
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* INTESTAZIONI EXPANDER SCURE */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
    }
    div[data-testid="stExpander"] summary p { color: #cbd5e1 !important; }

    /* TABELLE HTML PER CENTRATURA TOTALE */
    .table-main {
        width: 100%;
        border-collapse: collapse;
        margin: 0 auto;
        table-layout: fixed;
    }
    .table-main td {
        text-align: center;
        vertical-align: middle;
        padding: 5px;
    }

    /* Immagine con dimensione controllata */
    .bey-img {
        width: 180px !important;
        display: block;
        margin: 10px auto;
    }

    /* BOTTONI: Riconfigurati per stare in riga */
    .stButton button {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
        border: 1px solid #475569 !important;
        display: inline-flex;
    }

    /* Fix per tasto Aggiungi Tutto */
    .full-width-btn div[data-testid="stVerticalBlock"] > div:last-child button {
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ... (Funzioni load_db e get_img invariate) ...
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
        img = Image.open(path); img.thumbnail(size)
        return img
    return None

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
            
            # 1. TABELLA NOME E IMMAGINE (Centrata)
            st.markdown(f"""
                <div style="text-align:center;">
                    <h3 style="color:#60a5fa; margin-bottom:5px;">{row['name'].upper()}</h3>
                </div>
            """, unsafe_allow_html=True)
            
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                # Metodo più sicuro per centrare l'immagine senza farla esplodere
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.image(img, use_container_width=True)
            
            st.write("---")
            
            # 2. TABELLA COMPONENTI (2 Colonne, Centrate)
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Usiamo colonne ma forziamo il CSS per non farle andare a capo
                    # Questo è l'ultimo tentativo prima dell'HTML puro per i bottoni
                    c1, c2 = st.columns([0.7, 0.3])
                    c1.markdown(f"<div style='text-align:right; padding-top:5px;'>{val}</div>", unsafe_allow_html=True)
                    if c2.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            # 3. TASTO AGGIUNGI TUTTO (Largo quanto la card)
            st.write("")
            if st.button("Aggiungi tutto", key=f"all_{i}", use_container_width=True):
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