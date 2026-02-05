import streamlit as st
import pandas as pd
import hashlib
import os
import time
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE CSS
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Font e Font-size */
    html, body, [class*="st-"] { font-size: 1.1rem; }
    
    /* Container Card Aggiungi */
    .bey-card { 
        background-color: white; padding: 10px; border-radius: 12px; 
        border: 2px solid #e2e8f0; margin-bottom: 15px;
        display: flex; flex-direction: column; align-items: center;
    }
    
    .bey-name { font-weight: bold; font-size: 1.15rem; color: #0f172a; margin-bottom: 10px; text-align: center; width: 100%; }
    
    /* Layout Componenti: Nome a sinistra, Bottone a destra sulla stessa riga */
    .comp-row {
        display: flex; justify-content: space-between; align-items: center;
        width: 100%; padding: 4px 0; border-bottom: 1px solid #f1f5f9;
    }
    .comp-name { font-size: 0.95rem; color: #475569; text-align: left; flex-grow: 1; margin-right: 5px; }

    /* Forzatura 2 colonne su Mobile tramite Grid */
    .mobile-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
    }
    
    /* Centratura Immagini */
    .stImage > img { display: block; margin-left: auto; margin-right: auto; border-radius: 8px; }

    /* Bottoni compatti */
    .stButton>button { border-radius: 6px; padding: 2px 8px; }
    </style>
    """, unsafe_allow_html=True)

CSV_FILE = "beyblade_x.csv"
IMAGES_DIR = "images"

# =========================
# FUNZIONI CORE
# =========================
@st.cache_data
def load_db():
    if not os.path.exists(CSV_FILE): return pd.DataFrame()
    df = pd.read_csv(CSV_FILE).fillna("")
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df

@st.cache_resource
def get_img(url, size=(110, 110)):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join(IMAGES_DIR, f"{h}.png")
    if os.path.exists(path):
        img = Image.open(path)
        img.thumbnail(size)
        return img
    return None

# Inizializzazione Session State
if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}
if 'decks' not in st.session_state:
    st.session_state.decks = []

df = load_db()

# --- DEFINIZIONE UTENTE (Risolve NameError) ---
st.sidebar.title("🔧 Officina X")
utente = st.sidebar.selectbox("Utente", ["Antonio", "Andrea", "Fabio"])

# =========================
# UI PRINCIPALE
# =========================
tab_add, tab_inv, tab_deck = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

# --- TAB AGGIUNGI ---
with tab_add:
    search_input = st.text_input("Cerca...", key="search_main") # Tolto "(minimo 2 lettere)"
    
    filtered = df
    if len(search_input) >= 2:
        filtered = df[df['_search'].str.contains(search_input.lower())]
    elif len(search_input) == 1:
        filtered = df.head(0)
    else:
        filtered = df.head(8)

    # Utilizzo di un container per gestire la griglia 2-colonne
    st.markdown('<div class="mobile-grid">', unsafe_allow_html=True)
    
    # Per simulare le colonne in Streamlit senza che vadano a capo su mobile
    col_l, col_r = st.columns(2)
    
    for i, (_, row) in enumerate(filtered.iterrows()):
        target_col = col_l if i % 2 == 0 else col_r
        
        with target_col:
            st.markdown(f"""<div class='bey-card'>
                <div class='bey-name'>{row['name']}</div>""", unsafe_allow_html=True)
            
            # Immagine centrata
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img: 
                st.image(img, width=110)
            
            # Righe componenti con tasto "+" accanto
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    c_txt, c_btn = st.columns([4, 1.2])
                    c_txt.markdown(f"<div class='comp-name'>{val}</div>", unsafe_allow_html=True)
                    if c_btn.button("＋", key=f"add_{inv_key}_{i}_{val}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")
            
            st.write("") 
            if st.button("TUTTO", key=f"all_{i}"):
                for field, inv_key in comps:
                    if row[field] and row[field] != "n/a":
                        st.session_state.inventario[inv_key][row[field]] = st.session_state.inventario[inv_key].get(row[field], 0) + 1
                st.toast("Aggiunto Bey completo!")
            st.markdown("</div>", unsafe_allow_html=True)

# --- TAB INVENTARIO ---
with tab_inv:
    st.header(f"Inventario di {utente}")
    ordine = ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]
    
    for tipo in ordine:
        pezzi = st.session_state.inventario.get(tipo, {})
        if any(pezzi.values()):
            with st.expander(f"**{tipo.replace('_', ' ').upper()}**", expanded=True):
                for nome, qta in list(pezzi.items()):
                    if qta > 0:
                        ci1, ci2, ci3 = st.columns([4, 1, 1])
                        ci1.write(f"{nome} (x{qta})")
                        if ci2.button("＋", key=f"inv_plus_{tipo}_{nome}"):
                            st.session_state.inventario[tipo][nome] += 1
                            st.rerun()
                        if ci3.button("－", key=f"inv_min_{tipo}_{nome}"):
                            st.session_state.inventario[tipo][nome] -= 1
                            if st.session_state.inventario[tipo][nome] <= 0:
                                del st.session_state.inventario[tipo][nome]
                            st.rerun()

# --- TAB DECK ---
with tab_deck:
    col_h, col_b = st.columns([2, 1])
    col_h.header(f"Deck di {utente}")
    if col_b.button("➕ Nuovo Deck"):
        st.session_state.decks.append({"name": f"Deck {len(st.session_state.decks)+1}"})

    for d_idx, deck in enumerate(st.session_state.decks):
        with st.expander(f"📂 {deck['name']}", expanded=True):
            for b_idx in range(3):
                st.markdown(f"**BEY {b_idx+1}**")
                
                # Flag su una riga sola
                f1, f2, f3 = st.columns(3)
                cx = f1.checkbox("CX", key=f"cx_{d_idx}_{b_idx}")
                rib = f2.checkbox("RIB", key=f"rib_{d_idx}_{b_idx}")
                theory = f3.checkbox("Theory", key=f"th_{d_idx}_{b_idx}")
                
                rows = []
                if cx: rows += [("Lock Bit", "lock_chip", "lock_chip_image"), ("Main Blade", "main_blade", "main_blade_image"), ("Assist Blade", "assist_blade", "assist_blade_image")]
                else:  rows += [("Blade", "blade", "blade_image")]
                if rib: rows += [("R.I.B.", "ratchet_integrated_bit", "ratchet_integrated_bit_image")]
                else:   rows += [("Ratchet", "ratchet", "ratchet_image"), ("Bit", "bit", "bit_image")]

                for label, db_key, img_db_key in rows:
                    if theory:
                        opts = [""] + sorted(df[db_key].unique().tolist())
                    else:
                        inv_k = "lock_bit" if db_key == "lock_chip" else db_key
                        opts = [""] + sorted(list(st.session_state.inventario.get(inv_k, {}).keys()))
                    
                    cd1, cd2 = st.columns([3, 1])
                    scelta = cd1.selectbox(label, opts, key=f"sel_{d_idx}_{b_idx}_{db_key}")
                    
                    if scelta:
                        img_url = df[df[db_key] == scelta][img_db_key].values
                        if len(img_url) > 0:
                            p_img = get_img(img_url[0], size=(65, 65))
                            if p_img: cd2.image(p_img)