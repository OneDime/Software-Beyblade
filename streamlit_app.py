import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

# CSS Custom per card, bordi e layout
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    /* Card stile Tab Aggiungi */
    .bey-card { 
        background-color: white; 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #e2e8f0; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        text-align: center;
    }
    .bey-name { font-weight: bold; font-size: 1rem; color: #1e293b; margin-bottom: 8px; }
    .comp-text { font-size: 0.85rem; color: #64748b; line-height: 1.2; }
    
    /* Bottoni compatti */
    .stButton>button { border-radius: 8px; font-size: 0.8rem; }
    
    /* Ottimizzazione spazio Deck */
    [data-testid="stExpander"] { border: 1px solid #cbd5e1; background: white; }
    </style>
    """, unsafe_allow_html=True)

CSV_FILE = "beyblade_x.csv"
IMAGES_DIR = "images"

# =========================
# FUNZIONI OTTIMIZZATE
# =========================
@st.cache_data
def load_db():
    if not os.path.exists(CSV_FILE): return pd.DataFrame()
    df = pd.read_csv(CSV_FILE).fillna("")
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df

@st.cache_resource
def get_img(url, size=(100, 100)):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join(IMAGES_DIR, f"{h}.png")
    if os.path.exists(path):
        img = Image.open(path)
        img.thumbnail(size)
        return img
    return None

def add_to_inv(tipo, nome):
    if nome and nome != "n/a":
        st.session_state.inventario[tipo][nome] = st.session_state.inventario[tipo].get(nome, 0) + 1

# Inizializzazione Session State
if 'inventario' not in st.session_state:
    st.session_state.inventario = {
        "lock_bit": {}, "blade": {}, "main_blade": {}, "assist_blade": {},
        "ratchet": {}, "bit": {}, "ratchet_integrated_bit": {}
    }
if 'decks' not in st.session_state:
    st.session_state.decks = []

df = load_db()

# =========================
# UI SIDEBAR
# =========================
st.sidebar.title("🔧 Officina X")
utente = st.sidebar.selectbox("Utente", ["Antonio", "Andrea", "Fabio"])

# =========================
# TAB PRINCIPALI
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

# --- TAB 1: AGGIUNGI ---
with tab1:
    search_q = st.text_input("Cerca...", "").lower()
    filtered = df[df['_search'].str.contains(search_q)] if search_q else df
    
    # 2 colonne per cellulare, 4 per desktop
    n_cols = 2 if st.columns(2) else 4 
    cols = st.columns(2 if search_q else 2) # Forza 2 colonne per ordine cellulare
    
    for i, (_, row) in enumerate(filtered.iterrows()):
        col_idx = i % 2
        with cols[col_idx]:
            st.markdown(f"""<div class='bey-card'>
                <div class='bey-name'>{row['name']}</div>""", unsafe_allow_html=True)
            
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img: st.image(img, use_container_width=False, width=120)
            
            # Elenco componenti con tasto "+" singolo (Punto Aggiungi)
            comps = [
                ("lock_chip", "lock_bit"), ("blade", "blade"), 
                ("main_blade", "main_blade"), ("assist_blade", "assist_blade"),
                ("ratchet", "ratchet"), ("bit", "bit"), 
                ("ratchet_integrated_bit", "ratchet_integrated_bit")
            ]
            
            for field, inv_key in comps:
                nome_pezzo = row[field]
                if nome_pezzo and nome_pezzo != "n/a":
                    c_text, c_btn = st.columns([4, 1])
                    c_text.markdown(f"<div class='comp-text'>{nome_pezzo}</div>", unsafe_allow_html=True)
                    if c_btn.button("＋", key=f"add_{inv_key}_{i}"):
                        add_to_inv(inv_key, nome_pezzo)
                        st.toast(f"Aggiunto: {nome_pezzo}")
            
            st.divider()
            if st.button(f"Aggiungi Tutto", key=f"all_{i}"):
                for field, inv_key in comps:
                    add_to_inv(inv_key, row[field])
                st.toast("Intero Beyblade aggiunto!")
            st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: INVENTARIO ---
with tab2:
    st.header(f"Inventario di {utente}")
    # Ordine richiesto (Punto Inventario)
    ordine_inv = ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]
    
    for tipo in ordine_inv:
        pezzi = st.session_state.inventario[tipo]
        if pezzi:
            with st.expander(f"{tipo.replace('_', ' ').title()}", expanded=True):
                for nome, qta in pezzi.items():
                    st.write(f"**{qta}x** {nome}")

# --- TAB 3: DECK BUILDER ---
with tab3:
    header_col, btn_col = st.columns([3, 1])
    header_col.header(f"Deck di {utente}")
    if btn_col.button("➕ Nuovo Deck"):
        st.session_state.decks.append({"name": f"Deck {len(st.session_state.decks)+1}"})

    for d_idx, deck in enumerate(st.session_state.decks):
        with st.expander(f"📂 {deck['name']}", expanded=True):
            b_cols = st.columns(3)
            for b_idx in range(3):
                with b_cols[b_idx]:
                    st.markdown(f"**Bey {b_idx+1}**")
                    
                    # Flags su una riga (Punto Deck)
                    f1, f2, f3 = st.columns(3)
                    cx = f1.checkbox("CX", key=f"cx_{d_idx}_{b_idx}")
                    rib = f2.checkbox("RIB", key=f"rib_{d_idx}_{b_idx}")
                    theory = f3.checkbox("Theory", key=f"th_{d_idx}_{b_idx}")
                    
                    def select_part(label, key, img_key):
                        # Filtro opzioni
                        if theory:
                            opts = sorted(df[key].unique().tolist())
                        else:
                            inv_k = "lock_bit" if key == "lock_chip" else key
                            opts = sorted(list(st.session_state.inventario[inv_k].keys()))
                        
                        if not opts: opts = [""]
                        
                        sel = st.selectbox(label, opts, key=f"sel_{key}_{d_idx}_{b_idx}")
                        
                        # Mostra immagine (Punto Deck Immagini)
                        if sel:
                            img_url = df[df[key] == sel][img_key].values
                            if len(img_url) > 0:
                                p_img = get_img(img_url[0], size=(80, 80))
                                if p_img: st.image(p_img, width=70)
                        return sel

                    if cx:
                        select_part("Lock Bit", "lock_chip", "lock_chip_image")
                        select_part("Main Blade", "main_blade", "main_blade_image")
                        select_part("Assist Blade", "assist_blade", "assist_blade_image")
                    else:
                        select_part("Blade", "blade", "blade_image")
                    
                    if rib:
                        select_part("R.I.B.", "ratchet_integrated_bit", "ratchet_integrated_bit_image")
                    else:
                        select_part("Ratchet", "ratchet", "ratchet_image")
                        select_part("Bit", "bit", "bit_image")

    st.divider()
    if st.button("💾 SALVA TUTTI I DATI ONLINE"):
        st.success("Pronto per il collegamento finale a Google Sheets!")