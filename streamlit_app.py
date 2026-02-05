import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE DARK "OFFICINA"
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo Generale e Testi Tab/Ricerca */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* Rende i testi dei Tab e delle Label grigio chiaro/bianco */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stWidgetLabel"] p,
    .stTabs [data-baseweb="tab-panel"] p,
    label [data-testid="stWidgetLabel"] p, 
    .stMarkdown p { color: #f1f5f9 !important; font-weight: 500; }
    
    /* Input di ricerca: testo chiaro */
    input { color: #f1f5f9 !important; background-color: #1e293b !important; border: 1px solid #334155 !important; }

    /* CARD TOTALE: La "Scocca" che racchiude tutto */
    .bey-card-total {
        background-color: #1e293b; 
        border: 2px solid #3b82f6;
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 25px;
        text-align: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.5);
    }

    .bey-header {
        font-weight: bold;
        font-size: 1.4rem;
        color: #60a5fa;
        margin-bottom: 15px;
        text-transform: uppercase;
        border-bottom: 1px solid #334155;
        padding-bottom: 10px;
    }

    /* Riga Componenti: FORZA l'affiancamento senza andare a capo */
    .force-row {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        justify-content: space-between !important;
        align-items: center !important;
        width: 100% !important;
        background: #0f172a;
        margin: 6px 0;
        padding: 8px 12px;
        border-radius: 10px;
    }
    
    .comp-name-text {
        font-size: 0.95rem;
        color: #e2e8f0;
        text-align: left;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        flex-shrink: 1;
    }

    /* Bottoni Aggiungi (+) */
    .add-btn-style button {
        min-width: 35px !important;
        height: 35px !important;
        background-color: #3b82f6 !important;
        color: white !important;
        border-radius: 8px !important;
        flex-shrink: 0 !important;
    }

    /* Centratura Immagine */
    [data-testid="stImage"] { display: flex; justify-content: center; margin: 15px 0; }
    
    /* Deck Builder Fix */
    .deck-part-row {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 10px !important;
        width: 100% !important;
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
def get_img(url, size=(160, 160)):
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
    search_q = st.text_input("Cerca beyblade o componenti...", key="search_main")
    
    filtered = df
    if len(search_q) >= 2:
        filtered = df[df['_search'].str.contains(search_q.lower())]
    else:
        filtered = df.head(4)

    for i, (_, row) in enumerate(filtered.iterrows()):
        # INIZIO CARD UNIFICATA
        st.markdown(f'<div class="bey-card-total">', unsafe_allow_html=True)
        st.markdown(f'<div class="bey-header">{row["name"]}</div>', unsafe_allow_html=True)
        
        img = get_img(row['blade_image'] or row['beyblade_page_image'])
        if img: st.image(img, width=160)
        
        comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                 ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                 ("ratchet_integrated_bit", "ratchet_integrated_bit")]
        
        for field, inv_key in comps:
            val = row[field]
            if val and val != "n/a":
                # Layout per bloccare il tasto accanto al nome
                col_name, col_btn = st.columns([0.8, 0.2])
                with col_name:
                    st.markdown(f"<div class='comp-name-text'>{val}</div>", unsafe_allow_html=True)
                with col_btn:
                    if st.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

        st.markdown("<br>", unsafe_allow_html=True)
        # Fix tasto Aggiungi Tutto
        if st.button("Aggiungi tutto", key=f"all_btn_{i}", use_container_width=True):
            for field, inv_key in comps:
                v = row[field]
                if v and v != "n/a":
                    st.session_state.inventario[inv_key][v] = st.session_state.inventario[inv_key].get(v, 0) + 1
            st.toast(f"Aggiunto {row['name']} completo!")
            
        st.markdown('</div>', unsafe_allow_html=True) # FINE CARD UNIFICATA

with tab_inv:
    st.header(f"Inventario di {utente}")
    ordine = ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]
    for tipo in ordine:
        pezzi = st.session_state.inventario.get(tipo, {})
        validi = {k: v for k, v in pezzi.items() if v > 0}
        if validi:
            with st.expander(f"{tipo.replace('_', ' ').upper()}", expanded=True):
                for nome, qta in validi.items():
                    c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                    c1.write(f"{nome} (x{qta})")
                    if c2.button("＋", key=f"inv_p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if c3.button("－", key=f"inv_m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()

with tab_deck:
    st.header(f"Deck di {utente}")
    if st.button("➕ Nuovo Deck", use_container_width=True):
        st.session_state.decks.append({"name": f"Deck {len(st.session_state.decks)+1}"})

    for d_idx, deck in enumerate(st.session_state.decks):
        with st.expander(f"📂 {deck['name']}", expanded=True):
            for b_idx in range(3):
                st.markdown(f"#### Beyblade {b_idx+1}")
                
                # Flag sulla stessa riga
                f1, f2, f3 = st.columns(3)
                v_cx = f1.checkbox("CX", key=f"cx_{d_idx}_{b_idx}")
                v_rib = f2.checkbox("RIB", key=f"rib_{d_idx}_{b_idx}")
                v_th = f3.checkbox("Theory", key=f"th_{d_idx}_{b_idx}")
                
                rows = []
                if v_cx: rows += [("Lock Bit", "lock_chip", "lock_chip_image"), ("Main Blade", "main_blade", "main_blade_image"), ("Assist Blade", "assist_blade", "assist_blade_image")]
                else: rows += [("Blade", "blade", "blade_image")]
                if v_rib: rows += [("R.I.B.", "ratchet_integrated_bit", "ratchet_integrated_bit_image")]
                else: rows += [("Ratchet", "ratchet", "ratchet_image"), ("Bit", "bit", "bit_image")]

                for label, db_key, img_db_key in rows:
                    if v_th: opts = [""] + sorted(df[db_key].unique().tolist())
                    else:
                        inv_k = "lock_bit" if db_key == "lock_chip" else db_key
                        opts = [""] + sorted(list(st.session_state.inventario.get(inv_k, {}).keys()))
                    
                    # Layout Deck forzato: Menu e Immagine
                    cd1, cd2 = st.columns([0.7, 0.3])
                    scelta = cd1.selectbox(label, opts, key=f"s_{d_idx}_{b_idx}_{db_key}")
                    if scelta:
                        img_url = df[df[db_key] == scelta][img_db_key].values
                        if len(img_url) > 0:
                            p_img = get_img(img_url[0], size=(80, 80))
                            if p_img: cd2.image(p_img)