import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE (RIPRISTINATO)
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* INTESTAZIONI SCURE */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
    }
    div[data-testid="stExpander"] summary p { color: #cbd5e1 !important; }

    /* CENTRATURA TITOLI E IMMAGINI */
    .centered-text { text-align: center; width: 100%; }
    [data-testid="stImage"] img { display: block; margin-left: auto; margin-right: auto; }

    /* STILE BOTTONI */
    button {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
        border: 1px solid #475569 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# FUNZIONI CORE (RIPRISTINATE)
# =========================
@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame()
    df = pd.read_csv("beyblade_x.csv").fillna("")
    # Creiamo la colonna di ricerca per rendere la ricerca estemporanea fluida
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

df = load_db()

# =========================
# UI PRINCIPALE
# =========================
tab_add, tab_inv, tab_deck = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab_add:
    # Ricerca estemporanea ripristinata
    search_q = st.text_input("Cerca...", key="search_main")
    
    # Se la ricerca è vuota mostra i primi 3, altrimenti filtra in tempo reale
    if search_q:
        filtered = df[df['_search'].str.contains(search_q.lower())]
    else:
        filtered = df.head(3)

    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            # Titolo Centrato
            st.markdown(f"<h3 class='centered-text' style='color:#60a5fa;'>{row['name'].upper()}</h3>", unsafe_allow_html=True)
            
            # Immagine Centrata
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img: st.image(img, width=200)
            
            st.write("---") # Separatore visivo
            
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    # Layout pulito: Nome Componente | Bottone +
                    # Usiamo colonne standard di Streamlit senza forzature CSS distruttive
                    c1, c2 = st.columns([0.8, 0.2])
                    c1.write(val) # Ripristinato il nome della componente
                    if c2.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            st.write("") 
            if st.button("Aggiungi tutto", key=f"all_{i}", use_container_width=True):
                for field, inv_key in comps:
                    val = row[field]
                    if val and val != "n/a":
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                st.toast(f"Aggiunto set completo di {row['name']}")

with tab_inv:
    st.header("Inventario")
    for tipo in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]:
        pezzi = st.session_state.inventario.get(tipo, {})
        validi = {k: v for k, v in pezzi.items() if v > 0}
        
        if validi:
            with st.expander(tipo.replace('_', ' ').upper(), expanded=True):
                for nome, qta in validi.items():
                    # Layout: Nome (xQta) | + | -
                    ci1, ci2, ci3 = st.columns([0.6, 0.2, 0.2])
                    ci1.write(f"{nome} (x{qta})")
                    if ci2.button("＋", key=f"inv_p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if ci3.button("－", key=f"inv_m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()