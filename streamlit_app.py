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
    /* Sfondo Generale */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* INTESTAZIONI EXPANDER SCURE (INVENTARIO) */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }
    div[data-testid="stExpander"] summary { background-color: #1e293b !important; }
    div[data-testid="stExpander"] summary p { color: #cbd5e1 !important; }

    /* STILE TABELLE HTML PER COSTRUIRE LA CARD */
    .table-bey {
        width: 100%;
        border-collapse: collapse;
        margin: 0 auto;
    }
    .table-bey td {
        text-align: center;
        vertical-align: middle;
        padding: 10px;
    }

    /* Tabella Componenti: Forza l'allineamento affiancato */
    .table-comp {
        width: 100%;
        max-width: 300px; /* Impedisce che si allarghi troppo su desktop */
        margin: 0 auto;   /* Centra la tabella nella card */
        border-collapse: collapse;
    }
    .table-comp td {
        padding: 5px;
        vertical-align: middle;
    }
    .td-name {
        text-align: right; /* Nome componente spinge verso il centro */
        width: 70%;
        color: #f1f5f9;
        font-size: 0.95rem;
    }
    .td-btn {
        text-align: left; /* Tasto "+" spinge verso il centro */
        width: 30%;
    }

    /* Override Bottoni Streamlit per farli stare nella tabella */
    div.stButton > button {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
        border: 1px solid #475569 !important;
        padding: 0px 10px !important;
        height: 32px !important;
        width: 40px !important;
    }

    /* Centratura Immagine */
    .bey-img-container {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 150px;
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
            
            # --- PRIMA TABELLA: 1 COLONNA, 2 RIGHE (NOME E IMMAGINE) ---
            st.markdown(f"""
                <table class="table-bey">
                    <tr><td><h3 style="color:#60a5fa; margin:0; text-transform: uppercase;">{row['name']}</h3></td></tr>
                </table>
            """, unsafe_allow_html=True)
            
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                # Usiamo le colonne solo per l'immagine per tenerla piccola al centro
                _, img_col, _ = st.columns([1, 1, 1])
                img_col.image(img, use_container_width=True)
            
            st.markdown("<hr style='margin:10px 0; border:0; border-top:1px solid #334155;'>", unsafe_allow_html=True)
            
            # --- SECONDA TABELLA: 2 COLONNE (COMPONENTE E TASTO) ---
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Usiamo le colonne sbilanciate ma con allineamento forzato CSS
                    col_left, col_right = st.columns([0.65, 0.35])
                    col_left.markdown(f"<div style='text-align:right; padding-top:5px;'>{val}</div>", unsafe_allow_html=True)
                    if col_right.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            # --- TASTO AGGIUNGI TUTTO ---
            st.write("")
            if st.button("Aggiungi tutto", key=f"all_{i}", use_container_width=True):
                for f, k in comps:
                    if row[f] and row[f] != "n/a":
                        st.session_state.inventario[k][row[f]] = st.session_state.inventario[k].get(row[f], 0) + 1
                st.toast(f"Set {row['name']} aggiunto!")

with tab_inv:
    st.header("Inventario")
    for tipo in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]:
        pezzi = st.session_state.inventario.get(tipo, {})
        validi = {k: v for k, v in pezzi.items() if v > 0}
        if validi:
            with st.expander(tipo.replace('_', ' ').upper(), expanded=True):
                for nome, qta in validi.items():
                    c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                    c1.write(f"{nome} (x{qta})")
                    if c2.button("＋", key=f"inv_p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if c3.button("－", key=f"inv_m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()