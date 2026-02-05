import streamlit as st
import pandas as pd
import hashlib
import os
import json
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE (ORIGINALE)
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    
    .user-title { font-size: 28px !important; font-weight: bold; margin-bottom: 20px; color: #f1f5f9; }

    /* TAB AGGIUNGI (STILE ORIGINALE) */
    [data-testid="stVerticalBlock"] { text-align: center; align-items: center; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 15px !important;
        padding: 10px !important;
    }
    .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; }
    .comp-name-centered { font-size: 1.1rem; color: #cbd5e1; display: block; width: 100%; }
    hr { margin-top: 8px !important; margin-bottom: 8px !important; opacity: 0.3; }

    div.stButton > button {
        width: auto !important; min-width: 150px !important;
        height: 30px !important; background-color: #334155 !important; color: white !important;
        border: 1px solid #475569 !important; border-radius: 4px !important;
    }

    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; text-align: left !important; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# INIZIALIZZAZIONE DATI
# =========================
if 'users' not in st.session_state:
    st.session_state.users = {
        "Antonio": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]},
        "Andrea": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]},
        "Fabio": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]}
    }

@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame(), {}
    df = pd.read_csv("beyblade_x.csv").fillna("")
    img_map = {}
    for _, r in df.iterrows():
        for col in df.columns:
            if "_image" in col and r[col] and r[col] != "n/a":
                comp_col = col.replace("_image", "")
                if comp_col in df.columns: img_map[r[comp_col]] = r[col]
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df, img_map

def get_img(url, size=(100, 100)):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join("images", f"{h}.png")
    if os.path.exists(path):
        img = Image.open(path)
        return img.resize(size, Image.Resampling.LANCZOS)
    return None

df_db, global_img_map = load_db()

# =========================
# UI
# =========================
st.sidebar.title("👤 Account")
user_selected = st.sidebar.radio("Seleziona Utente:", ["Antonio", "Andrea", "Fabio"])
user_data = st.session_state.users[user_selected]

st.markdown(f"<div class='user-title'>Officina di {user_selected}</div>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab1:
    search_q = st.text_input("Cerca...", "").lower()
    filtered = df_db[df_db['_search'].str.contains(search_q)] if search_q else df_db.head(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.markdown(f"<div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
            img = get_img(row['blade_image'] or row['beyblade_page_image'], size=(150, 150))
            if img: st.image(img)
            components = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"),
                          ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"),
                          ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                for ck, ik in components:
                    val = row[ck]
                    if val and val != "n/a": user_data["inv"][ik][val] = user_data["inv"][ik].get(val, 0) + 1
                st.rerun()
            st.markdown("<hr>", unsafe_allow_html=True)
            for ck, ik in components:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name-centered'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        user_data["inv"][ik][val] = user_data["inv"][ik].get(val, 0) + 1
                        st.rerun()

with tab2:
    for cat, items in user_data["inv"].items():
        if items:
            with st.expander(cat.upper()):
                for n, q in items.items():
                    st.write(f"{n}: {q}")

with tab3:
    st.write("Seleziona i tuoi Beyblade qui.")