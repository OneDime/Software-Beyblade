import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# Configurazione Pagina
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

# Costanti
CSV_FILE = "beyblade_x.csv"
IMAGES_DIR = "images"

# Caricamento Database
@st.cache_data
def load_data():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame()
    return pd.read_csv(CSV_FILE).fillna("")

df = load_data()

def get_img(url):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join(IMAGES_DIR, f"{h}.png")
    if os.path.exists(path):
        return Image.open(path)
    return None

# Sidebar con Utenti
st.sidebar.title("👤 Utente")
utente = st.sidebar.selectbox("Chi sta usando l'app?", ["Antonio", "Andrea", "Fabio"])

# Menu principale
tab1, tab2, tab3 = st.tabs(["🔍 Cerca e Aggiungi", "📦 Inventario", "📋 I miei Deck"])

with tab1:
    st.header("Aggiungi all'Inventario")
    search = st.text_input("Cerca Beyblade o parte...")
    
    if search:
        # Filtro potente su tutte le colonne
        filtered = df[df.apply(lambda row: search.lower() in row.astype(str).str.lower().values, axis=1)]
    else:
        filtered = df.head(10)

    # Griglia automatica
    cols = st.columns(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                st.subheader(row['name'])
                img = get_img(row['blade_image'] or row['beyblade_page_image'])
                if img: st.image(img, use_container_width=True)
                if st.button(f"➕ Aggiungi tutto", key=f"btn_{i}"):
                    st.success(f"Aggiunto a {utente}!")

with tab3:
    st.header(f"Configurazione Deck - {utente}")
    
    for d_idx in range(1, 2): # Iniziamo con 1 deck per prova
        st.subheader(f"Slot Deck {d_idx}")
        b_cols = st.columns(3)
        
        for b_idx in range(3):
            with b_cols[b_idx]:
                with st.expander(f"Beyblade {b_idx+1}", expanded=True):
                    cx = st.checkbox("CX", key=f"cx_{d_idx}_{b_idx}")
                    rib = st.checkbox("RIB", key=f"rib_{d_idx}_{b_idx}")
                    
                    if cx:
                        st.selectbox("Lock Bit", df['lock_chip'].unique(), key=f"lb_{d_idx}_{b_idx}")
                        st.selectbox("Main Blade", df['main_blade'].unique(), key=f"mb_{d_idx}_{b_idx}")
                        st.selectbox("Assist Blade", df['assist_blade'].unique(), key=f"ab_{d_idx}_{b_idx}")
                    else:
                        st.selectbox("Blade", df['blade'].unique(), key=f"bl_{d_idx}_{b_idx}")
                    
                    if rib:
                        st.selectbox("R.I.B.", df['ratchet_integrated_bit'].unique(), key=f"ri_{d_idx}_{b_idx}")
                    else:
                        st.selectbox("Ratchet", df['ratchet'].unique(), key=f"ra_{d_idx}_{b_idx}")
                        st.selectbox("Bit", df['bit'].unique(), key=f"bi_{d_idx}_{b_idx}")

    if st.button("💾 SALVA DECK ONLINE"):
        st.warning("Il salvataggio su Google Sheets sarà attivo tra poco!")