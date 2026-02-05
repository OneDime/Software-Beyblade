import streamlit as st
import pandas as pd
import hashlib
import os
import json
from PIL import Image
import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIGURAZIONE & STILE (RIPRISTINATO E INTOCCABILE)
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    
    /* TITOLO UTENTE */
    .user-title { font-size: 28px !important; font-weight: bold; margin-bottom: 20px; color: #f1f5f9; }

    /* STILI TAB AGGIUNGI (RIPRISTINO ORIGINALE) */
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

    /* BOTTONI AGGIUNGI */
    div.stButton > button {
        width: auto !important; min-width: 150px !important;
        height: 30px !important; background-color: #334155 !important; color: white !important;
        border: 1px solid #475569 !important; border-radius: 4px !important;
    }

    /* STILE EXPANDER */
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; text-align: left !important; margin-bottom: 5px !important; }
    
    /* SIDEBAR CUSTOM */
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# CONNESSIONE GOOGLE SHEETS (VIA GSPREAD)
# =========================
# ID del foglio (preso dall'URL che hai postato)
SPREADSHEET_ID = "1VW5TUbrvnHnSn9WCbmrkCfOgUo85et4jQK9pSgTrdkM"

def get_gspread_client():
    # Per semplicità in questa fase usiamo le credenziali dai Secrets di Streamlit
    # Devi incollare il contenuto del tuo JSON di Service Account nei Secrets
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        return gspread.authorize(creds)
    except:
        return None

def load_cloud_data():
    client = get_gspread_client()
    data = {u: {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, 
                "decks": [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]} for u in ["Antonio", "Andrea", "Fabio"]}
    
    if client:
        try:
            sh = client.open_by_key(SPREADSHEET_ID)
            # Carica Inventario
            ws_inv = sh.worksheet("inventario")
            df_inv = pd.DataFrame(ws_inv.get_all_records())
            # Carica Decks
            ws_decks = sh.worksheet("decks")
            df_decks = pd.DataFrame(ws_decks.get_all_records())
            
            for user in data.keys():
                u_inv = df_inv[df_inv["Utente"] == user]
                if not u_inv.empty: data[user]["inv"] = json.loads(u_inv.iloc[0]["Dati_JSON"])
                u_decks = df_decks[df_decks["Utente"] == user]
                if not u_decks.empty: data[user]["decks"] = json.loads(u_decks.iloc[0]["Dati_JSON"])
        except Exception as e:
            st.error(f"Errore caricamento: {e}")
    return data

def save_cloud_data():
    client = get_gspread_client()
    if not client: return
    
    try:
        sh = client.open_by_key(SPREADSHEET_ID)
        
        # Salva Inventario
        ws_inv = sh.worksheet("inventario")
        inv_data = [["Utente", "Dati_JSON"]]
        for user in ["Antonio", "Andrea", "Fabio"]:
            inv_data.append([user, json.dumps(st.session_state.users[user]["inv"])])
        ws_inv.update(inv_data)
        
        # Salva Decks
        ws_decks = sh.worksheet("decks")
        deck_data = [["Utente", "Dati_JSON"]]
        for user in ["Antonio", "Andrea", "Fabio"]:
            deck_data.append([user, json.dumps(st.session_state.users[user]["decks"])])
        ws_decks.update(deck_data)
    except Exception as e:
        st.error(f"Errore salvataggio: {e}")

# =========================
# LOGICA APP (IL RESTO RIMANE UGUALE)
# =========================
if 'users' not in st.session_state:
    st.session_state.users = load_cloud_data()

st.sidebar.title("👤 Account")
user_selected = st.sidebar.radio("Seleziona Utente:", ["Antonio", "Andrea", "Fabio"])

user_data = st.session_state.users[user_selected]
inventario_corrente = user_data["inv"]
decks_correnti = user_data["decks"]

if 'exp_state' not in st.session_state: st.session_state.exp_state = {}
if 'edit_name_idx' not in st.session_state: st.session_state.edit_name_idx = None

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

df_db, global_img_map = load_db()

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
                    if val and val != "n/a": inventario_corrente[ik][val] = inventario_corrente[ik].get(val, 0) + 1
                save_cloud_data()
                st.rerun()
            st.markdown("<hr>", unsafe_allow_html=True)
            for ck, ik in components:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name-centered'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        inventario_corrente[ik][val] = inventario_corrente[ik].get(val, 0) + 1
                        save_cloud_data()
                        st.rerun()

# [Le Tab 2 e 3 rimangono identiche, con save_cloud_data() richiamato dopo ogni modifica]
# ... (Codice per Tab 2 e Tab 3) ...