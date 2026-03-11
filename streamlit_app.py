import streamlit as st
import pandas as pd
import hashlib
import os
import json
import requests
import base64
import time
from datetime import datetime
from PIL import Image
import google.generativeai as genai  # <-- Libreria Gemini

# =========================
# CONFIGURAZIONE & STILE (Invariato)
# =========================
def inject_css():
    st.markdown("""
        <style>
        :root { color-scheme: dark; }
        .stApp { background-color: #0f172a; color: #f1f5f9; }
        .user-title { font-size: 28px !important; font-weight: bold; margin-bottom: 20px; color: #f1f5f9; text-align: center; width: 100%; }
        [data-testid="stVerticalBlock"] { gap: 0.5rem !important; text-align: center; align-items: center; }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 2px solid #334155 !important;
            background-color: #1e293b !important;
            border-radius: 12px !important;
            margin-bottom: 15px !important;
            padding: 10px !important;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; text-align: center; width: 100%; }
        .comp-name-centered { font-size: 1.1rem; color: #cbd5e1; text-align: center; width: 100%; display: block; margin-top: 5px; }
        hr { margin-top: 8px !important; margin-bottom: 8px !important; opacity: 0.3; width: 100%; }
        div.stButton > button { width: auto !important; min-width: 150px !important; height: 30px !important; background-color: #334155 !important; color: white !important; border: 1px solid #475569 !important; border-radius: 4px !important; }
        .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; text-align: left !important; margin-bottom: 5px !important; }
        [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
        .slot-summary-box {
            background-color: #0f172a; border-left: 4px solid #60a5fa;
            padding: 8px 12px; margin: 4px 0px; border-radius: 4px;
            text-align: left; width: 100%;
        }
        .slot-summary-name { font-weight: bold; color: #f1f5f9; text-transform: uppercase; }
        .slot-summary-alert { color: #fbbf24; font-weight: bold; margin-left: 8px; font-size: 0.85rem; }
        .ai-response-area { 
            background-color: #1e293b; border: 1px solid #60a5fa; 
            padding: 20px; border-radius: 10px; color: #f1f5f9;
            line-height: 1.6; text-align: left;
        }
        </style>
        """, unsafe_allow_html=True)

st.set_page_config(page_title="Officina Beyblade X", layout="wide", initial_sidebar_state="expanded")
inject_css()

# =========================
# LOGICA GITHUB & GEMINI
# =========================
GITHUB_TOKEN = st.secrets["github_token"]
REPO = st.secrets["github_repo"]
GEMINI_KEY = st.secrets.get("gemini_api_key") # Aggiungi nei secrets di Streamlit
FILES = {"inv": "inventario.json", "decks": "decks.json"}

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

def github_action(file_key, data=None, method="GET"):
    ts = int(time.time())
    url = f"https://api.github.com/repos/{REPO}/contents/{FILES[file_key]}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        r_get = requests.get(f"{url}?t={ts}", headers=headers)
        sha = r_get.json().get("sha") if r_get.status_code == 200 else None
        if method == "GET":
            if r_get.status_code == 200:
                return json.loads(base64.b64decode(r_get.json()["content"]).decode('utf-8'))
            return None
        elif method == "PUT":
            payload = {"message": f"App Update {FILES[file_key]}", "content": base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8'), "sha": sha}
            return requests.put(url, headers=headers, json=payload).status_code in [200, 201]
    except: return False
    return False

# ... [Funzioni force_load, save_cloud, load_db, get_img rimangono invariate] ...

# (Assumiamo che le funzioni siano qui come nel tuo file originale)
def force_load():
    inv_c = github_action("inv", method="GET")
    deck_c = github_action("decks", method="GET")
    new_users = {}
    for u in ["Antonio", "Andrea", "Fabio"]:
        new_users[u] = {
            "inv": inv_c.get(u, {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}) if inv_c else {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]},
            "decks": deck_c.get(u, [{"name": "DECK 1", "slots": {"0":{"tipo":"BX/UX"}, "1":{"tipo":"BX/UX"}, "2":{"tipo":"BX/UX"}}}]) if deck_c else [{"name": "DECK 1", "slots": {"0":{"tipo":"BX/UX"}, "1":{"tipo":"BX/UX"}, "2":{"tipo":"BX/UX"}}}]
        }
    st.session_state.users = new_users

def save_cloud():
    inv_data = {u: d["inv"] for u, d in st.session_state.users.items()}
    deck_data = {u: d["decks"] for u, d in st.session_state.users.items()}
    if github_action("inv", inv_data, "PUT") and github_action("decks", deck_data, "PUT"):
        st.toast("✅ Dati salvati!", icon="💾")
    else: st.error("❌ Errore sincronizzazione")

if 'users' not in st.session_state:
    force_load()

valid_users = ["Antonio", "Andrea", "Fabio"]
url_user = st.query_params.get("user")
if url_user in valid_users and 'user_sel' not in st.session_state:
    st.session_state.user_sel = url_user
    force_load()

if 'user_sel' not in st.session_state:
    @st.dialog("Accesso Officina")
    def user_dialog():
        st.write("Seleziona utente:")
        for u in valid_users:
            if st.button(u, use_container_width=True):
                st.session_state.user_sel = u
                st.query_params["user"] = u 
                force_load(); st.rerun()
    user_dialog(); st.stop()

@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame(), {}, {}
    df = pd.read_csv("beyblade_x.csv").fillna("")
    img_map = {}
    theory_opts = {}
    mapping = [('lock_chip', 'lock_chip_image', 'lock_bit'), ('blade', 'blade_image', 'blade'), 
               ('main_blade', 'main_blade_image', 'main_blade'), ('assist_blade', 'assist_blade_image', 'assist_blade'), 
               ('ratchet', 'ratchet_image', 'ratchet'), ('bit', 'bit_image', 'bit'), 
               ('ratchet_integrated_bit', 'ratchet_integrated_bit_image', 'ratchet_integrated_bit')]
    for csv_col, img_col, state_key in mapping:
        if csv_col in df.columns:
            theory_opts[state_key] = ["-"] + sorted([x for x in df[csv_col].unique().tolist() if x and x != "n/a"])
            if img_col in df.columns:
                for _, r in df.iterrows():
                    if r[csv_col] and r[csv_col] != "n/a": img_map[r[csv_col]] = r[img_col]
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df, img_map, theory_opts

@st.cache_resource
def get_img(url, size=(100, 100)):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join("images", f"{h}.png")
    if os.path.exists(path):
        return Image.open(path).resize(size, Image.Resampling.LANCZOS)
    return None

df_db, global_img_map, theory_opts = load_db()
user_sel = st.session_state.user_sel
user_data = st.session_state.users[user_sel]

# ... [Tab 1, 2, 3 rimangono invariate] ...
# (Per brevità salto il codice delle prime 3 tab che hai già)

tab1, tab2, tab3, tab4 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder", "🤖 AI Advisor"])

# --- (Ometti qui il codice di Tab 1, 2, 3 per brevità) ---

# --- TAB 4: AI ADVISOR ---
with tab4:
    st.markdown("### 🤖 Strategia & Ottimizzazione Deck")
    
    if not GEMINI_KEY:
        st.warning("⚠️ Gemini API Key non trovata. Aggiungi 'gemini_api_key' nei Secrets.")
    
    with st.container(border=True):
        col_a, col_b = st.columns(2)
        with col_a:
            tipo_deck_ai = st.selectbox("Tipo di Deck", ["Aggro puro", "Anti-meta", "Stamina dominante", "Difensivo / Counter", "Top meta ottimizzato", "Equilibrato", "High-risk High-reward", "Tech specialist"])
            lancio_ai = st.select_slider("Capacità di Lancio", options=list(range(1, 11)), value=5)
            torneo_ai = st.selectbox("Livello Torneo", ["Locale", "Regionale", "Nazionale", "WBO competitivo"])

        with col_b:
            all_owned_components = ["nessuna"]
            for cat in user_data["inv"]:
                all_owned_components.extend(sorted(user_data["inv"][cat].keys()))
            comp_obbligatoria = st.selectbox("Componente Obbligatoria", all_owned_components)
            comp_escludere = st.selectbox("Componente da Escludere", all_owned_components)

        if st.button("🚀 GENERA STRATEGIA GEMINI", use_container_width=True) and GEMINI_KEY:
            with st.spinner("Gemini sta analizzando il meta..."):
                try:
                    # Prepariamo l'inventario testuale per l'IA
                    inv_text = json.dumps(user_data["inv"], indent=2)
                    
                    prompt = f"""
                    Sei un esperto mondiale di Beyblade X. Analizza questo inventario e crea un deck da 3 slot.
                    Inventario disponibile: {inv_text}
                    Obiettivo: {tipo_deck_ai}
                    Livello Torneo: {torneo_ai}
                    Capacità Lancio Utente: {lancio_ai}/10
                    Obbligatorio usare: {comp_obbligatoria}
                    Escludere assolutamente: {comp_escludere}
                    
                    Rispondi in italiano. Per ogni Beyblade specifica:
                    1. Nome e Combo (Blade, Ratchet, Bit)
                    2. Perché questa combo è efficace nel meta attuale.
                    3. Consigli sul lancio.
                    """
                    
                    response = model.generate_content(prompt)
                    st.session_state.last_ai_resp = response.text
                except Exception as e:
                    st.error(f"Errore Gemini: {e}")

    if 'last_ai_resp' in st.session_state:
        st.markdown(f"<div class='ai-response-area'>{st.session_state.last_ai_resp}</div>", unsafe_allow_html=True)