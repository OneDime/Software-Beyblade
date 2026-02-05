import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE CSS ESTREMO
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Forza 2 colonne su smartphone */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 10px !important;
    }
    
    /* Card completa con bordo e ombra */
    .bey-card-container {
        background-color: white;
        border: 2px solid #d1d5db;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        display: flex;
        flex-direction: column;
        align-items: center;
        min-height: 450px;
    }

    .bey-name-header {
        font-weight: bold;
        background-color: #1e3a8a;
        color: white;
        width: 100%;
        text-align: center;
        padding: 8px 0;
        border-radius: 10px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 50px;
    }

    /* Righe componenti: forza testo e tasto sulla stessa riga sempre */
    .row-flex {
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-between !important;
        align-items: center !important;
        width: 100% !important;
        margin-bottom: 8px;
    }

    /* Fix immagini e selectbox nel Deck */
    .deck-row {
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        margin-bottom: 10px;
    }
    
    .stSelectbox { flex-grow: 1; }
    
    /* Centratura immagini */
    .stImage > img { display: block; margin: 0 auto; }
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
def get_img(url, size=(100, 100)):
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
# UI
# =========================
tab_add, tab_inv, tab_deck = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab_add:
    # Per rendere la ricerca "più" estemporanea usiamo il parametro on_change in futuro, 
    # per ora ottimizziamo il filtro.
    search_q = st.text_input("Cerca...", key="search_bar")
    
    filtered = df
    if len(search_q) >= 2:
        filtered = df[df['_search'].str.contains(search_q.lower())]
    else:
        filtered = df.head(6)

    # Layout a 2 colonne reali (anche su mobile)
    col_a, col_b = st.columns(2)
    for i, (_, row) in enumerate(filtered.iterrows()):
        target = col_a if i % 2 == 0 else col_b
        with target:
            st.markdown(f'<div class="bey-card-container">', unsafe_allow_html=True)
            st.markdown(f'<div class="bey-name-header">{row["name"]}</div>', unsafe_allow_html=True)
            
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img: st.image(img, width=110)
            
            st.write("") # Spacer
            
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Usiamo colonne piccolissime per forzare l'affiancamento
                    c_txt, c_btn = st.columns([0.8, 0.2])
                    c_txt.markdown(f"**{val}**")
                    if c_btn.button("＋", key=f"btn_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")
            
            st.write("")
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                for f, k in comps:
                    if row[f] and row[f] != "n/a":
                        st.session_state.inventario[k][row[f]] = st.session_state.inventario[k].get(row[f], 0) + 1
                st.toast("Bey aggiunto!")
            st.markdown('</div>', unsafe_allow_html=True)

with tab_inv:
    st.header(f"Inventario di {utente}")
    ordine = ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]
    for tipo in ordine:
        pezzi = st.session_state.inventario.get(tipo, {})
        if any(pezzi.values()):
            with st.expander(f"{tipo.replace('_', ' ').upper()}", expanded=True):
                for nome, qta in list(pezzi.items()):
                    if qta > 0:
                        # Forza affiancamento tasti in inventario
                        c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                        c1.write(f"{nome} (x{qta})")
                        if c2.button("＋", key=f"inv+_{tipo}_{nome}"):
                            st.session_state.inventario[tipo][nome] += 1
                            st.rerun()
                        if c3.button("－", key=f"inv-_{tipo}_{nome}"):
                            st.session_state.inventario[tipo][nome] -= 1
                            st.rerun()

with tab_deck:
    col_h, col_b = st.columns([2, 1])
    col_h.header(f"Deck di {utente}")
    if col_b.button("➕ Nuovo Deck"):
        st.session_state.decks.append({"name": f"Deck {len(st.session_state.decks)+1}"})

    for d_idx, deck in enumerate(st.session_state.decks):
        with st.expander(f"📂 {deck['name']}", expanded=True):
            for b_idx in range(3):
                st.subheader(f"Beyblade {b_idx+1}")
                
                # Flag affiancati
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
                    
                    # Layout Deck: Menu e Immagine sulla stessa riga
                    cd1, cd2 = st.columns([0.75, 0.25])
                    scelta = cd1.selectbox(label, opts, key=f"s_{d_idx}_{b_idx}_{db_key}")
                    if scelta:
                        img_url = df[df[db_key] == scelta][img_db_key].values
                        if len(img_url) > 0:
                            p_img = get_img(img_url[0], size=(70, 70))
                            if p_img: cd2.image(p_img)