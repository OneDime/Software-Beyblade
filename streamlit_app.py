import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & CSS TABELLE
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
    div[data-testid="stExpander"] summary { background-color: #1e293b !important; }
    div[data-testid="stExpander"] summary p { color: #cbd5e1 !important; font-weight: bold; }

    /* STILE TABELLE */
    .table-container {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 10px;
    }
    .table-container td {
        vertical-align: middle;
        text-align: center;
        padding: 8px;
    }
    
    /* Tabella componenti: allineamento specifico */
    .comp-table td:first-child {
        text-align: right; /* Nome componente a destra verso il centro */
        width: 70%;
        padding-right: 15px;
    }
    .comp-table td:last-child {
        text-align: left; /* Tasto a sinistra verso il centro */
        width: 30%;
    }

    /* Immagine centrata */
    .beyblade-img {
        width: 150px;
        height: auto;
        display: block;
        margin: 0 auto;
    }

    /* Bottoni scuri */
    button {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
        border: 1px solid #475569 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ... (Funzioni load_db e get_img identiche) ...
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
            # --- PRIMA TABELLA: NOME E IMMAGINE ---
            st.markdown(f"""
                <table class="table-container">
                    <tr><td><h3 style="color:#60a5fa; margin:0;">{row['name'].upper()}</h3></td></tr>
                </table>
            """, unsafe_allow_html=True)
            
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                st.image(img) # Streamlit centra già se impostato nel CSS sopra

            # --- SECONDA TABELLA: COMPONENTI + TASTI ---
            # Nota: Streamlit non permette bottoni dentro HTML puro facilmente, 
            # quindi usiamo le colonne per simulare la tabella con centratura verticale.
            st.write("") 
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    c1, c2 = st.columns([0.7, 0.3])
                    # Usiamo markdown per centrare verticalmente il testo nella cella "invisibile"
                    c1.markdown(f"<div style='text-align:right; padding-top:8px;'>{val}</div>", unsafe_allow_html=True)
                    if c2.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            # --- TASTO AGGIUNGI TUTTO ---
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