import streamlit as st
import pandas as pd
import hashlib
import os
import time
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE CSS AVANZATO
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Font generale e sfondi */
    html, body, [class*="st-"] { font-size: 1.05rem; }
    .stApp { background-color: #f1f5f9; }
    
    /* Card Aggiungi */
    .bey-card { 
        background-color: white; padding: 15px; border-radius: 12px; 
        border: 2px solid #e2e8f0; margin-bottom: 20px; text-align: center;
    }
    .bey-name { font-weight: bold; font-size: 1.2rem; color: #0f172a; margin-bottom: 10px; text-align: center; }
    
    /* Griglia componenti in 2 colonne */
    .comp-grid {
        display: grid; grid-template-columns: 1fr 1fr; gap: 8px; 
        align-items: center; justify-items: center; margin-top: 10px;
    }
    .comp-item { font-size: 0.95rem; color: #475569; text-align: center; }

    /* Bottoni e controlli */
    .stButton>button { width: 100%; border-radius: 6px; }
    .small-btn>div>button { padding: 2px 5px; height: 28px; width: 28px; font-size: 0.8rem; }
    
    /* Forzatura flag inline per Mobile */
    [data-testid="column"] { min-width: 0px !important; }
    .stCheckbox { margin-bottom: 0px; }
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
def get_img(url, size=(90, 90)):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join(IMAGES_DIR, f"{h}.png")
    if os.path.exists(path):
        img = Image.open(path)
        img.thumbnail(size)
        return img
    return None

# Inizializzazione Session State (Memoria locale)
if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}
if 'decks' not in st.session_state:
    st.session_state.decks = []

df = load_db()

# =========================
# UI PRINCIPALE
# =========================
tab_add, tab_inv, tab_deck = st.tabs(["➕ Aggiungi", "📦 Inventario", "🧩 Deck"])

# --- TAB AGGIUNGI ---
with tab_add:
    # Ricerca con delay e soglia caratteri
    search_input = st.text_input("Cerca (minimo 2 lettere)...", key="search_main")
    
    filtered = df
    if len(search_input) >= 2:
        time.sleep(0.1) # Piccolo delay per non appesantire
        filtered = df[df['_search'].str.contains(search_input.lower())]
    elif len(search_input) == 1:
        st.caption("Continua a scrivere...")
        filtered = df.head(0) # Non mostrare nulla con 1 lettera
    else:
        filtered = df.head(10) # Default iniziale

    cols = st.columns(2) # Forza 2 colonne per mobile
    for i, (_, row) in enumerate(filtered.iterrows()):
        with cols[i % 2]:
            st.markdown(f"<div class='bey-card'><div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img: st.image(img, use_container_width=False, width=100)
            
            # Griglia Componenti (Punto: 2 colonne e "+" accanto)
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            st.markdown("<div class='comp-grid'>", unsafe_allow_html=True)
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"<div class='comp-item'>{val}</div>", unsafe_allow_html=True)
                    if c2.button("＋", key=f"add_{inv_key}_{i}_{val}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.write("") # Spaziatore
            if st.button("Aggiungi Tutto", key=f"all_{i}"):
                for field, inv_key in comps:
                    if row[field] and row[field] != "n/a":
                        st.session_state.inventario[inv_key][row[field]] = st.session_state.inventario[inv_key].get(row[field], 0) + 1
                st.toast("Beyblade completo aggiunto!")
            st.markdown("</div>", unsafe_allow_html=True)

# --- TAB INVENTARIO ---
with tab_inv:
    st.header("Il tuo Inventario")
    ordine = ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]
    
    for tipo in ordine:
        pezzi = st.session_state.inventario[tipo]
        if any(pezzi.values()): # Mostra solo se ci sono pezzi con qta > 0
            with st.expander(f"**{tipo.replace('_', ' ').upper()}**", expanded=True):
                for nome, qta in list(pezzi.items()):
                    if qta > 0:
                        c1, c2, c3 = st.columns([4, 1, 1])
                        c1.write(f"{nome} (x{qta})")
                        if c2.button("＋", key=f"inv_plus_{tipo}_{nome}"):
                            st.session_state.inventario[tipo][nome] += 1
                            st.rerun()
                        if c3.button("－", key=f"inv_min_{tipo}_{nome}"):
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
                st.markdown(f"--- **BEYBLADE {b_idx+1}** ---")
                
                # Flag inline (Forzatura colonne strette)
                f1, f2, f3 = st.columns([1, 1, 1.5])
                cx = f1.checkbox("CX", key=f"cx_{d_idx}_{b_idx}")
                rib = f2.checkbox("RIB", key=f"rib_{d_idx}_{b_idx}")
                theory = f3.checkbox("Theory", key=f"th_{d_idx}_{b_idx}")
                
                rows = []
                if cx: rows += [("Lock Bit", "lock_chip", "lock_chip_image"), ("Main Blade", "main_blade", "main_blade_image"), ("Assist Blade", "assist_blade", "assist_blade_image")]
                else:  rows += [("Blade", "blade", "blade_image")]
                
                if rib: rows += [("R.I.B.", "ratchet_integrated_bit", "ratchet_integrated_bit_image")]
                else:   rows += [("Ratchet", "ratchet", "ratchet_image"), ("Bit", "bit", "bit_image")]

                for label, db_key, img_db_key in rows:
                    # Logica opzioni (Theory o Inventario)
                    if theory:
                        opts = [""] + sorted(df[db_key].unique().tolist())
                    else:
                        inv_k = "lock_bit" if db_key == "lock_chip" else db_key
                        opts = [""] + sorted(list(st.session_state.inventario[inv_k].keys()))
                    
                    # Layout Componente + Immagine ACCOANTO
                    c_sel, c_img = st.columns([3, 1])
                    scelta = c_sel.selectbox(label, opts, key=f"sel_{d_idx}_{b_idx}_{db_key}")
                    
                    if scelta:
                        img_url = df[df[db_key] == scelta][img_db_key].values
                        if len(img_url) > 0:
                            p_img = get_img(img_url[0], size=(60, 60))
                            if p_img: c_img.image(p_img)

    st.button("💾 SALVATAGGIO CLOUD (Prossimo Step)")