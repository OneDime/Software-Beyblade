import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & FIX COLORI SMARTPHONE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo generale scuro */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* FIX TESTI: Forza grigio chiaro su tab e label */
    .stTabs [data-baseweb="tab-list"] button p, 
    label p, .stMarkdown p, .stSelectbox p { 
        color: #f1f5f9 !important; 
    }

    /* FIX BOTTONI: Devono essere scuri con testo bianco su ogni dispositivo */
    button, [data-testid="stBaseButton-secondary"] {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 8px !important;
    }

    /* Centratura totale dei widget nel container */
    [data-testid="stVerticalBlock"] > div {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }

    /* Forza l'allineamento orizzontale dei componenti (Nome + Bottone) */
    .comp-box {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        max-width: 350px;
        background: #0f172a;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    
    /* Fix per evitare che le immagini vadano sotto nei selectbox del deck */
    [data-testid="column"] {
        display: flex !important;
        align-items: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# LOGICA DATI
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
# UI PRINCIPALE
# =========================
tab_add, tab_inv, tab_deck = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab_add:
    search_q = st.text_input("Cerca...", placeholder="Inserisci nome o componente")
    
    filtered = df
    if len(search_q) >= 2:
        filtered = df[df['_search'].str.contains(search_q.lower())]
    else:
        filtered = df.head(3)

    for i, (_, row) in enumerate(filtered.iterrows()):
        # USO DI ST.CONTAINER CON BORDO: Risolve il problema della "forma vuota"
        with st.container(border=True):
            st.subheader(row["name"].upper())
            
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                st.image(img, width=180)
            
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Layout Nome + Bottone centrato e scuro
                    c_txt, c_btn = st.columns([0.8, 0.2])
                    c_txt.markdown(f"**{val}**")
                    if c_btn.button("＋", key=f"btn_add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            st.write("")
            if st.button("Aggiungi tutto", key=f"all_{i}", use_container_width=True):
                for f, k in comps:
                    if row[f] and row[f] != "n/a":
                        st.session_state.inventario[k][row[f]] = st.session_state.inventario[k].get(row[f], 0) + 1
                st.toast("Beyblade aggiunto!")

with tab_inv:
    st.header(f"Inventario: {utente}")
    for tipo in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]:
        pezzi = {k: v for k, v in st.session_state.inventario.get(tipo, {}).items() if v > 0}
        if pezzi:
            with st.expander(tipo.replace('_', ' ').upper(), expanded=True):
                for nome, qta in pezzi.items():
                    c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                    c1.write(f"{nome} (x{qta})")
                    if c2.button("＋", key=f"p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if c3.button("－", key=f"m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()

with tab_deck:
    st.header(f"Deck Builder: {utente}")
    if st.button("➕ Crea Nuovo Deck", use_container_width=True):
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
                    if v_th: opts = [""] + sorted(df[db_key].unique().tolist())
                    else:
                        inv_k = "lock_bit" if db_key == "lock_chip" else db_key
                        opts = [""] + sorted(list(st.session_state.inventario.get(inv_k, {}).items())) # Fix opzioni inventario
                        opts = [o[0] for o in opts if o[1] > 0]
                    
                    c_sel, c_img = st.columns([0.7, 0.3])
                    scelta = c_sel.selectbox(label, [""] + opts, key=f"dk_{d_idx}_{b_idx}_{db_key}")
                    if scelta:
                        img_url = df[df[db_key] == scelta][img_db_key].values
                        if len(img_url) > 0:
                            p_img = get_img(img_url[0], size=(80, 80))
                            if p_img: c_img.image(p_img)