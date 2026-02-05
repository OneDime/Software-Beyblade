import streamlit as st
import pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & FIX DEFINITIVO BORDI
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo Generale */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* FIX INTESTAZIONI */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }
    div[data-testid="stExpander"] summary p { color: #cbd5e1 !important; }
    div[data-testid="stExpander"] summary { background-color: #1e293b !important; border-radius: 10px; }

    /* CENTRATURA IMMAGINE */
    [data-testid="stImage"] { display: flex; justify-content: center; width: 100%; }
    [data-testid="stImage"] img { margin: 0 auto !important; }

    /* FIX LAYOUT: Impedisce il taglio a destra */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        width: 100% !important;
        padding-right: 10px !important; /* Spazio per non tagliare i tasti */
    }

    /* Colonna Testo: prende tutto lo spazio tranne quello dei bottoni */
    div[data-testid="column"]:nth-of-type(1) {
        flex: 1 1 auto !important;
        min-width: 0 !important;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Colonne Bottoni: larghezza fissa per evitare il taglio */
    div[data-testid="column"]:nth-of-type(2), 
    div[data-testid="column"]:nth-of-type(3) {
        flex: 0 0 50px !important; /* Blocca la larghezza a 50px */
        min-width: 50px !important;
        display: flex !important;
        justify-content: center !important;
    }

    /* Ripristino Bottoni Standard scuri */
    button {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
        border: 1px solid #475569 !important;
        min-width: 40px !important;
        height: 35px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ... (Funzioni load_db e get_img identiche a prima) ...

# =========================
# UI PRINCIPALE
# =========================
tab_add, tab_inv, tab_deck = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab_add:
    search_q = st.text_input("Cerca...", key="search_main")
    filtered = df[df['_search'].str.contains(search_q.lower())].head(3) if len(search_q) >= 2 else df.head(3)

    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.markdown(f"<h3 style='text-align:center; color:#60a5fa;'>{row['name'].upper()}</h3>", unsafe_allow_html=True)
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img: st.image(img, width=200)
            
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Layout: Testo | Bottone
                    c1, c2 = st.columns([0.8, 0.2])
                    c1.write(val)
                    if c2.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            st.button("Aggiungi tutto", key=f"all_{i}", use_container_width=True)

with tab_inv:
    st.header("Inventario")
    for tipo in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]:
        pezzi = st.session_state.inventario.get(tipo, {})
        validi = {k: v for k, v in pezzi.items() if v > 0}
        
        if validi:
            with st.expander(tipo.replace('_', ' ').upper(), expanded=True):
                for nome, qta in validi.items():
                    # Layout: Nome | + | -
                    ci1, ci2, ci3 = st.columns([0.6, 0.2, 0.2])
                    ci1.write(f"{nome} (x{qta})")
                    if ci2.button("＋", key=f"inv_p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if ci3.button("－", key=f"inv_m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()