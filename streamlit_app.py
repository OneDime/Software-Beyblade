import streamlit as st
import pandas as pd
import hashlib
import os
import json
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# =========================
# CONFIGURAZIONE & STILE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    .user-title { font-size: 28px !important; font-weight: bold; margin-bottom: 20px; color: #f1f5f9; }
    [data-testid="stVerticalBlock"] { text-align: center; align-items: center; gap: 0.5rem !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 15px !important;
        padding: 10px !important;
    }
    .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; }
    .comp-name-centered { font-size: 1.1rem; color: #cbd5e1; display: block; width: 100%; }
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; text-align: left !important; }
    div.stButton > button {
        width: auto !important; min-width: 150px !important;
        height: 30px !important; background-color: #334155 !important; color: white !important;
        border: 1px solid #475569 !important; border-radius: 4px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# CONNESSIONE GOOGLE SHEETS
# =========================
# URL del tuo foglio
SHEET_URL = "https://docs.google.com/spreadsheets/d/1VW5TUbrvnHnSn9WCbmrkCfOgUo85et4jQK9pSgTrdkM/edit?gid=0#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

def load_cloud_data():
    """Carica i dati dal foglio Google"""
    try:
        df_inv = conn.read(spreadsheet=SHEET_URL, worksheet="inventario")
        df_decks = conn.read(spreadsheet=SHEET_URL, worksheet="decks")
        
        data = {}
        for user in ["Antonio", "Andrea", "Fabio"]:
            # Default se l'utente non esiste nel foglio
            inv_init = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}
            deck_init = [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]
            
            # Cerca nel foglio inventario
            u_inv = df_inv[df_inv["Utente"] == user]
            if not u_inv.empty:
                inv_init = json.loads(u_inv.iloc[0]["Dati_JSON"])
                
            # Cerca nel foglio decks
            u_decks = df_decks[df_decks["Utente"] == user]
            if not u_decks.empty:
                deck_init = json.loads(u_decks.iloc[0]["Dati_JSON"])
                
            data[user] = {"inv": inv_init, "decks": deck_init}
        return data
    except:
        # Fallback se il foglio è vuoto o non raggiungibile
        return {u: {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, 
                    "decks": [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]} for u in ["Antonio", "Andrea", "Fabio"]}

def save_cloud_data():
    """Salva i dati correnti sul foglio Google"""
    # Prepara DataFrame per Inventario
    inv_rows = []
    deck_rows = []
    for user, content in st.session_state.users.items():
        inv_rows.append({"Utente": user, "Dati_JSON": json.dumps(content["inv"])})
        deck_rows.append({"Utente": user, "Dati_JSON": json.dumps(content["decks"])})
    
    conn.update(spreadsheet=SHEET_URL, worksheet="inventario", data=pd.DataFrame(inv_rows))
    conn.update(spreadsheet=SHEET_URL, worksheet="decks", data=pd.DataFrame(deck_rows))

# =========================
# LOGICA APP
# =========================
if 'users' not in st.session_state:
    st.session_state.users = load_cloud_data()

# Selezione Utente
user_selected = st.sidebar.radio("Seleziona Utente:", ["Antonio", "Andrea", "Fabio"])
user_data = st.session_state.users[user_selected]

# Funzione per eseguire azione e salvare
def trigger_action():
    save_cloud_data()
    st.rerun()

# [Caricamento DB locale per immagini e ricerca]
@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame(), {}
    df = pd.read_csv("beyblade_x.csv").fillna("")
    img_map = {}
    for _, r in df.iterrows():
        for col in ['lock_chip_image', 'blade_image', 'ratchet_image', 'bit_image']:
            if col in df.columns and r[col]: img_map[r[col.replace('_image', '')]] = r[col]
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df, img_map

df_db, global_img_map = load_db()

# ... (Implementazione Tab 1, 2, 3 come prima) ...

# ESEMPIO DI TRIGGER SALVATAGGIO (da applicare a ogni bottone):
# Se aggiungi un pezzo:
# st.session_state.users[user_selected]["inv"][cat][nome] += 1
# trigger_action() # Salva e ricarica