import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE "MOBILE-FIRST"
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* FIX INTESTAZIONI: Finalmente scure e leggibili */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
    }
    div[data-testid="stExpander"] summary p { color: #cbd5e1 !important; font-weight: bold; }

    /* FIX CENTRATURA IMMAGINE */
    [data-testid="stImage"] { text-align: center !important; display: flex !important; justify-content: center !important; }
    [data-testid="stImage"] img { margin: 0 auto !important; border-radius: 10px; }

    /* FIX RIGHE COMPONENTI: Impedisce sovrapposizioni */
    .comp-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        padding: 5px 0;
        border-bottom: 1px solid #1e293b;
    }

    /* Forza i bottoni a non allargarsi e non sovrapporsi */
    div[data-testid="column"] {
        width: fit-content !important;
        flex: unset !important;
        min-width: unset !important;
    }
    
    /* Spaziatura tra i bottoni + e - nell'inventario */
    div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 10px !important;
    }

    button {
        background-color: #1e293b !important;
        border: 1px solid #3b82f6 !important;
        color: white !important;
        padding: 2px 15px !important;
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
st.sidebar.title("🔧 Officina X")
utente = st.sidebar.selectbox("Utente", ["Antonio", "Andrea", "Fabio"])

# =========================
# TABS
# =========================
tab_add, tab_inv, tab_deck = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab_add:
    search_q = st.text_input("Cerca...", key="search_main")
    
    filtered = df
    if len(search_q) >= 2:
        filtered = df[df['_search'].str.contains(search_q.lower())]
    else:
        filtered = df.head(3)

    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.markdown(f"<h3 style='text-align:center;'>{row['name'].upper()}</h3>", unsafe_allow_html=True)
            
            # Centratura immagine corretta
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                st.image(img, width=180)
            
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Layout con colonne sbilanciate per evitare sovrapposizioni
                    c_txt, c_btn = st.columns([0.8, 0.2])
                    c_txt.markdown(f"<div style='padding-top:8px;'>{val}</div>", unsafe_allow_html=True)
                    if c_btn.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

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
                    # Layout Inventario: Nome | + | - 
                    # Usiamo colonne molto piccole per i tasti per tenerli vicini tra loro e a destra
                    ci1, ci2, ci3 = st.columns([0.6, 0.2, 0.2])
                    ci1.markdown(f"<div style='padding-top:8px;'>{nome} (x{qta})</div>", unsafe_allow_html=True)
                    if ci2.button("＋", key=f"inv_p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if ci3.button("－", key=f"inv_m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()

with tab_deck:
    # (Logica Deck Builder invariata ma ora beneficia dei fix CSS generali)
    st.header(f"Deck Builder")
    if st.button("➕ Nuovo Deck", use_container_width=True):
        st.session_state.decks.append({"name": f"Deck {len(st.session_state.decks)+1}"})

    for d_idx, deck in enumerate(st.session_state.decks):
        with st.expander(f"📂 {deck['name']}", expanded=True):
            for b_idx in range(3):
                st.markdown(f"<div style='text-align:center;'><b>BEY {b_idx+1}</b></div>", unsafe_allow_html=True)
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
                        opts = [""] + sorted([k for k, v in st.session_state.inventario.get(inv_k, {}).items() if v > 0])
                    
                    cd1, cd2 = st.columns([0.8, 0.2])
                    scelta = cd1.selectbox(label, opts, key=f"dk_{d_idx}_{b_idx}_{db_key}")
                    if scelta:
                        img_url = df[df[db_key] == scelta][img_db_key].values
                        if len(img_url) > 0:
                            p_img = get_img(img_url[0], size=(60, 60))
                            if p_img: cd2.image(p_img)