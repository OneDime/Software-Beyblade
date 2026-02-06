import streamlit as st
import pandas as pd
import hashlib
import os
import json
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# =========================
# CONFIGURAZIONE & STILE (IL TUO ORIGINALE)
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    .user-title { font-size: 28px !important; font-weight: bold; margin-bottom: 20px; color: #f1f5f9; }
    [data-testid="stVerticalBlock"] { text-align: center; align-items: center; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 15px !important;
        padding: 10px !important;
    }
    .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; text-align: center; }
    .comp-name-centered { font-size: 1.1rem; color: #cbd5e1; text-align: center; width: 100%; display: block; }
    hr { margin-top: 8px !important; margin-bottom: 8px !important; opacity: 0.3; }
    div.stButton > button {
        width: auto !important; min-width: 150px !important;
        height: 30px !important; background-color: #334155 !important; color: white !important;
        border: 1px solid #475569 !important; border-radius: 4px !important;
    }
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; text-align: left !important; margin-bottom: 5px !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# LOGICA SALVATAGGIO CLOUD
# =========================
def save_cloud():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Trasformiamo i dati in DataFrame per il foglio
        all_data = []
        for user, data in st.session_state.users.items():
            all_data.append({
                "Utente": user, 
                "Inventario": json.dumps(data["inv"]), 
                "Decks": json.dumps(data["decks"])
            })
        df_save = pd.DataFrame(all_data)
        # Aggiorna il foglio (deve esistere un foglio chiamato "Dati")
        conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=df_save)
    except Exception as e:
        st.sidebar.error(f"Errore salvataggio: {e}")

# =========================
# LOGICA DATI & IMMAGINI (TUA)
# =========================
@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame(), {}
    df = pd.read_csv("beyblade_x.csv").fillna("")
    img_map = {}
    mapping_rules = [('lock_chip', 'lock_chip_image'), ('blade', 'blade_image'), ('main_blade', 'main_blade_image'), 
                     ('assist_blade', 'assist_blade_image'), ('ratchet', 'ratchet_image'), ('bit', 'bit_image'),
                     ('ratchet_integrated_bit', 'ratchet_integrated_bit_image')]
    for comp_col, img_col in mapping_rules:
        if comp_col in df.columns and img_col in df.columns:
            for _, r in df.iterrows():
                nome, url = r[comp_col], r[img_col]
                if nome and nome != "n/a": img_map[nome] = url
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

# =========================
# GESTIONE ACCOUNT
# =========================
if 'users' not in st.session_state:
    st.session_state.users = {
        "Antonio": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]},
        "Andrea": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]},
        "Fabio": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]}
    }

st.sidebar.title("👤 Account")
user_selected = st.sidebar.radio("Seleziona Utente:", ["Antonio", "Andrea", "Fabio"])
user_data = st.session_state.users[user_selected]

if 'exp_state' not in st.session_state: st.session_state.exp_state = {}
if 'edit_name_idx' not in st.session_state: st.session_state.edit_name_idx = None

df_data, global_img_map = load_db()

# =========================
# UI PRINCIPALE (IDENTICA ALLA TUA)
# =========================
st.markdown(f"<div class='user-title'>Officina di {user_selected}</div>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab1:
    search_q = st.text_input("Cerca...", "").lower()
    filtered = df_data[df_data['_search'].str.contains(search_q)] if search_q else df_data.head(3)
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
                save_cloud() # AUTO-SALVA
                st.toast(f"Aggiunto a {user_selected}!")
            st.markdown("<hr>", unsafe_allow_html=True)
            for ck, ik in components:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name-centered'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        user_data["inv"][ik][val] = user_data["inv"][ik].get(val, 0) + 1
                        save_cloud() # AUTO-SALVA
                        st.toast(f"Aggiunto: {val}")

with tab2:
    modo = st.radio("L", ["Aggiungi (+1)", "Rimuovi (-1)"], horizontal=True, label_visibility="collapsed")
    operazione = 1 if "Aggiungi" in modo else -1
    for categoria, pezzi in user_data["inv"].items():
        if pezzi:
            with st.expander(categoria.replace('_', ' ').upper()):
                for nome, qta in pezzi.items():
                    if st.button(f"{nome} x{qta}", key=f"inv_{user_selected}_{categoria}_{nome}"):
                        user_data["inv"][categoria][nome] += operazione
                        if user_data["inv"][categoria][nome] <= 0: del user_data["inv"][categoria][nome]
                        save_cloud() # AUTO-SALVA
                        st.rerun()

with tab3:
    # --- QUI MANTIENI LA TUA LOGICA DECK BUILDER INTEGRALE ---
    # Ricordati solo di aggiungere save_cloud() dopo ogni modifica ai deck (rinomina, cambio pezzi, elimina)
    st.info("Logica Deck Builder attiva. Assicurati di chiamare save_cloud() dopo le modifiche.")