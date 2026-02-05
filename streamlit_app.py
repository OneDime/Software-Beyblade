import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo Generale */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* --- STILI TAB AGGIUNGI (INTOCCABILI) --- */
    [data-testid="stVerticalBlock"] {
        text-align: center;
        align-items: center;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 25px !important;
        padding: 15px !important;
    }

    .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; margin-bottom: 8px; text-align: center; }
    .comp-name-centered { font-size: 1.1rem; color: #cbd5e1; margin-top: 5px; margin-bottom: 2px; text-align: center; width: 100%; display: block; }

    /* Bottoni Tab Aggiungi */
    div.stButton > button {
        width: auto !important; 
        min-width: 150px !important; 
        padding-left: 40px !important;  
        padding-right: 40px !important;
        height: 30px !important;
        min-height: 30px !important;
        max-height: 30px !important;
        background-color: #334155 !important;
        color: white !important;
        border: 1px solid #475569 !important;
        border-radius: 4px !important;
        font-size: 1.1rem !important;
        line-height: 1 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        white-space: nowrap !important;
    }

    /* --- STILI TAB INVENTARIO (PERSONALIZZATI) --- */
    
    /* Riduzione altezza area Switch (Radio) */
    div[data-testid="stWidgetLabel"] {
        display: none !important; /* Nasconde l'etichetta dello switch per risparmiare spazio */
    }
    
    div[data-testid="stRadio"] > div {
        padding: 0px !important;
        margin-top: -15px !important;
        margin-bottom: -15px !important;
    }

    /* Allineamento componenti a sinistra nell'inventario */
    .inv-row-container {
        text-align: left !important;
        width: 100%;
        padding-left: 10px;
    }

    .inv-row button {
        width: 100% !important;
        justify-content: flex-start !important;
        background: transparent !important;
        border: none !important;
        color: #f1f5f9 !important;
        text-align: left !important;
        font-size: 1.1rem !important;
        height: 35px !important; /* Leggermente più alto per il touch */
        padding-left: 0px !important;
    }
    
    .inv-row button:hover {
        background: #334155 !important;
    }

    /* Expander Style */
    .stExpander { 
        border: 1px solid #334155 !important; 
        background-color: #1e293b !important; 
        text-align: left !important;
    }
    
    /* Fix per forzare l'allineamento a sinistra dentro gli expander */
    .stExpander [data-testid="stVerticalBlock"] {
        align-items: flex-start !important;
        text-align: left !important;
    }

    </style>
    """, unsafe_allow_html=True)

# =========================
# FUNZIONI UTILI
# =========================
@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame()
    df = pd.read_csv("beyblade_x.csv").fillna("")
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df

def get_img(url):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join("images", f"{h}.png")
    if os.path.exists(path): return Image.open(path)
    return None

def add_to_inv(tipo, nome, delta=1):
    if nome and nome != "n/a":
        if nome not in st.session_state.inventario[tipo]:
            st.session_state.inventario[tipo][nome] = 0
        st.session_state.inventario[tipo][nome] += delta
        if st.session_state.inventario[tipo][nome] <= 0:
            del st.session_state.inventario[tipo][nome]

if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}

df = load_db()

# =========================
# UI PRINCIPALE
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "Inventario", "🧩 Deck Builder"])

# --- TAB 1: AGGIUNGI (INTOCCABILE) ---
with tab1:
    search_q = st.text_input("Cerca...", "").lower()
    filtered = df[df['_search'].str.contains(search_q)] if search_q else df.head(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.markdown(f"<div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img: st.image(img, width=150)
            
            components = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"),
                          ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"),
                          ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            st.write("")
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                for ck, ik in components:
                    if row[ck] and row[ck] != "n/a": add_to_inv(ik, row[ck])
                st.toast("Set aggiunto!")
            st.markdown("<hr style='border-top: 1px solid #475569; margin: 15px 0;'>", unsafe_allow_html=True)
            for ck, ik in components:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name-centered'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        add_to_inv(ik, val)
                        st.toast(f"Aggiunto: {val}")

# --- TAB 2: INVENTARIO (SINISTRA & SWITCH COMPATTO) ---
with tab2:
    # Switch modalità ridotto
    modo = st.radio("Label_Hidden", ["Aggiungi (+1)", "Rimuovi (-1)"], horizontal=True, label_visibility="collapsed")
    operazione = 1 if "Aggiungi" in modo else -1
    
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    
    has_content = any(len(v) > 0 for v in st.session_state.inventario.values())
            
    if not has_content:
        st.info("L'inventario è vuoto.")
    else:
        for categoria, pezzi in st.session_state.inventario.items():
            if pezzi:
                cat_label = categoria.replace('_', ' ').upper()
                with st.expander(cat_label, expanded=False):
                    # Forziamo il contenitore dell'expander a sinistra
                    st.markdown('<div class="inv-row-container">', unsafe_allow_html=True)
                    for nome, qta in pezzi.items():
                        st.markdown('<div class="inv-row">', unsafe_allow_html=True)
                        if st.button(f"{nome} x{qta}", key=f"inv_{categoria}_{nome}"):
                            add_to_inv(categoria, nome, operazione)
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: DECK BUILDER ---
with tab3:
    st.info("Area Deck Builder in fase di allestimento...")