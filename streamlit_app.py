import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE "HARD-FIX"
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo e centratura generale */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* FIX INTESTAZIONI BIANCHE: Forza il colore su TUTTI i livelli dell'expander */
    .streamlit-expanderHeader, .streamlit-expanderHeader p, .streamlit-expanderHeader span, 
    div[data-testid="stExpander"] details summary p {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        font-weight: bold !important;
    }
    
    /* Centratura titolo e immagine */
    .bey-title { text-align: center; color: #60a5fa; font-size: 1.5rem; font-weight: bold; margin-bottom: 15px; }
    [data-testid="stImage"] > img { display: block; margin: 0 auto !important; }

    /* RIGA COMPONENTE: Flexbox per forzare l'affiancamento su mobile */
    .flex-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        max-width: 400px;
        margin: 0 auto 8px auto; /* Centra la riga nella card */
        padding: 5px 10px;
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
    }
    .flex-text { color: #f1f5f9; font-size: 0.95rem; flex-grow: 1; text-align: left; }

    /* BOTTONI: Piccoli e coerenti */
    button, [data-testid="stBaseButton-secondary"] {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 1px solid #3b82f6 !important;
        padding: 0px 12px !important;
        min-height: 32px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Funzione per generare la riga con il tasto accanto (senza usare st.columns)
def riga_componente(nome, chiave_pulsante, label_pulsante="＋"):
    # Usiamo st.columns ma forziamo il CSS per non farli andare a capo
    c1, c2 = st.columns([0.8, 0.2])
    with c1:
        st.markdown(f"<div style='padding-top:5px; text-align:left;'>{nome}</div>", unsafe_allow_html=True)
    with c2:
        return st.button(label_pulsante, key=chiave_pulsante)

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
# UI TABS
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
            st.markdown(f"<div class='bey-title'>{row['name'].upper()}</div>", unsafe_allow_html=True)
            
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img:
                st.image(img, width=200)
            
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Forza l'affiancamento ignorando il wrap di Streamlit
                    col1, col2 = st.columns([0.8, 0.2])
                    col1.markdown(f"<div style='text-align:left; font-size:0.9rem; padding-top:6px;'>{val}</div>", unsafe_allow_html=True)
                    if col2.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            st.write("")
            if st.button("Aggiungi tutto", key=f"all_{i}", use_container_width=True):
                for f, k in comps:
                    if row[f] and row[f] != "n/a":
                        st.session_state.inventario[k][row[f]] = st.session_state.inventario[k].get(row[f], 0) + 1
                st.toast("Beyblade aggiunto!")

with tab_inv:
    st.header(f"Inventario di {utente}")
    for tipo in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]:
        pezzi = st.session_state.inventario.get(tipo, {})
        validi = {k: v for k, v in pezzi.items() if v > 0}
        
        if validi:
            with st.expander(tipo.replace('_', ' ').upper(), expanded=True):
                for nome, qta in validi.items():
                    # Layout orizzontale forzato per inventario
                    c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                    c1.markdown(f"<div style='text-align:left; padding-top:6px;'>{nome} (x{qta})</div>", unsafe_allow_html=True)
                    if c2.button("＋", key=f"inv_p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if c3.button("－", key=f"inv_m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()

with tab_deck:
    st.header(f"Deck Builder")
    if st.button("➕ Nuovo Deck", use_container_width=True):
        st.session_state.decks.append({"name": f"Deck {len(st.session_state.decks)+1}"})

    for d_idx, deck in enumerate(st.session_state.decks):
        with st.expander(f"📂 {deck['name']}", expanded=True):
            for b_idx in range(3):
                st.markdown(f"<div style='text-align:center; font-weight:bold; padding:10px;'>BEYBLADE {b_idx+1}</div>", unsafe_allow_html=True)
                
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
                    if v_th: 
                        opts = [""] + sorted(df[db_key].unique().tolist())
                    else:
                        inv_k = "lock_bit" if db_key == "lock_chip" else db_key
                        inv_data = st.session_state.inventario.get(inv_k, {})
                        opts = [""] + sorted([k for k, v in inv_data.items() if v > 0])
                    
                    # Layout Deck: Selettore a sinistra, immagine a destra
                    cd1, cd2 = st.columns([0.75, 0.25])
                    scelta = cd1.selectbox(label, opts, key=f"dk_{d_idx}_{b_idx}_{db_key}")
                    if scelta:
                        img_url = df[df[db_key] == scelta][img_db_key].values
                        if len(img_url) > 0:
                            p_img = get_img(img_url[0], size=(80, 80))
                            if p_img: cd2.image(p_img)