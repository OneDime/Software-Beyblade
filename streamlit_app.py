import streamlit as st
import pandas as pd
import hashlib
import os
import json
import requests
import base64
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
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
    div.stButton > button { width: auto !important; min-width: 150px !important; height: 35px !important; background-color: #334155 !important; color: white !important; border: 1px solid #475569 !important; border-radius: 4px !important; }
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; text-align: left !important; margin-bottom: 5px !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# LOGICA GITHUB (NON TOCCARE)
# =========================
GITHUB_TOKEN = st.secrets["github_token"]
REPO = st.secrets["github_repo"]
FILES = {"inv": "inventario.json", "decks": "decks.json"}

def github_action(file_key, data=None, method="GET"):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILES[file_key]}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(url, headers=headers)
        sha = r.json().get("sha") if r.status_code == 200 else None
        if method == "GET":
            if r.status_code == 200:
                content = base64.b64decode(r.json()["content"]).decode('utf-8')
                return json.loads(content)
            return None
        elif method == "PUT":
            payload = {
                "message": f"Update {FILES[file_key]}",
                "content": base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8'),
                "sha": sha
            }
            res = requests.put(url, headers=headers, json=payload)
            return res.status_code
    except Exception as e:
        st.error(f"GitHub Error: {e}")
    return None

def save_cloud_manual():
    inv_data = {u: d["inv"] for u, d in st.session_state.users.items()}
    deck_data = {u: d["decks"] for u, d in st.session_state.users.items()}
    github_action("inv", inv_data, "PUT")
    status = github_action("decks", deck_data, "PUT")
    if status in [200, 201]:
        st.toast("✅ Sincronizzato con GitHub!")
    else:
        st.error("Errore durante il salvataggio.")

def load_cloud():
    inv_cloud = github_action("inv", method="GET")
    deck_cloud = github_action("decks", method="GET")
    if inv_cloud and deck_cloud:
        new_users = {}
        for u in ["Antonio", "Andrea", "Fabio"]:
            new_users[u] = {
                "inv": inv_cloud.get(u, {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}),
                "decks": deck_cloud.get(u, [{"name": "DECK 1", "slots": {str(i): {} for i in range(3)}}])
            }
        return new_users
    return None

# =========================
# DATI & IMMAGINI
# =========================
@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame(), {}
    df = pd.read_csv("beyblade_x.csv").fillna("")
    img_map = {}
    mapping = [('lock_chip', 'lock_chip_image'), ('blade', 'blade_image'), ('main_blade', 'main_blade_image'), 
               ('assist_blade', 'assist_blade_image'), ('ratchet', 'ratchet_image'), ('bit', 'bit_image'),
               ('ratchet_integrated_bit', 'ratchet_integrated_bit_image')]
    for c, im in mapping:
        if c in df.columns and im in df.columns:
            for _, r in df.iterrows():
                if r[c] and r[c] != "n/a": img_map[r[c]] = r[im]
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df, img_map

def get_img(url, size=(100, 100)):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join("images", f"{h}.png")
    if os.path.exists(path): return Image.open(path).resize(size, Image.Resampling.LANCZOS)
    return None

# =========================
# INIZIALIZZAZIONE
# =========================
if 'users' not in st.session_state:
    cloud = load_cloud()
    st.session_state.users = cloud if cloud else {u: {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {str(i): {} for i in range(3)}}]} for u in ["Antonio", "Andrea", "Fabio"]}

st.sidebar.title("👤 Account")
user_sel = st.sidebar.radio("Seleziona Utente:", ["Antonio", "Andrea", "Fabio"])
user_data = st.session_state.users[user_sel]
df_db, global_img_map = load_db()

# =========================
# UI PRINCIPALE
# =========================
st.markdown(f"<div class='user-title'>Officina di {user_sel}</div>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab1:
    search_q = st.text_input("Cerca...", "").lower()
    filtered = df_db[df_db['_search'].str.contains(search_q)] if search_q else df_db.head(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.markdown(f"<div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
            img = get_img(row['blade_image'] or row['beyblade_page_image'], size=(150, 150))
            if img: st.image(img)
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"),
                         ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"),
                         ("ratchet_integrated_bit", "ratchet_integrated_bit")]
                for ck, ik in comps:
                    val = row[ck]
                    if val and val != "n/a": user_data["inv"][ik][val] = user_data["inv"][ik].get(val, 0) + 1
                save_cloud_manual()

with tab2:
    modo = st.radio("Azione", ["Aggiungi (+1)", "Rimuovi (-1)"], horizontal=True)
    op = 1 if "Aggiungi" in modo else -1
    for cat, items in user_data["inv"].items():
        if items:
            with st.expander(cat.replace('_', ' ').upper()):
                for n, q in list(items.items()):
                    if st.button(f"{n} x{q}", key=f"inv_{user_sel}_{cat}_{n}"):
                        user_data["inv"][cat][n] += op
                        if user_data["inv"][cat][n] <= 0: del user_data["inv"][cat][n]
                        save_cloud_manual(); st.rerun()

with tab3:
    # TASTO SALVATAGGIO MANUALE (Unica via per aggiornare GitHub)
    if st.button("💾 SALVA MODIFICHE DECK", type="primary", use_container_width=True):
        save_cloud_manual()

    def get_options(cat, theory=False):
        if theory:
            csv_m = {"lock_bit": "lock_chip", "blade": "blade", "main_blade": "main_blade", "assist_blade": "assist_blade", "ratchet": "ratchet", "bit": "bit", "ratchet_integrated_bit": "ratchet_integrated_bit"}
            return ["-"] + sorted([x for x in df_db[csv_m.get(cat, cat)].unique().tolist() if x and x != "n/a"])
        return ["-"] + sorted(list(user_data["inv"][cat].keys()))

    tipologie = ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", "BX/UX Theory", "CX Theory", "BX/UX+RIB Theory", "CX+RIB Theory"]
    
    for d_idx, deck in enumerate(user_data["decks"]):
        with st.expander(f"📁 {deck['name'].upper()}", expanded=True):
            for s_idx in range(3):
                s_key = str(s_idx)
                if s_key not in deck["slots"]: deck["slots"][s_key] = {}
                curr_vals = deck["slots"][s_key]
                
                # Titolo dinamico
                titolo_parti = [v for v in curr_vals.values() if v and v != "-"]
                titolo = " ".join(titolo_parti) if titolo_parti else f"SLOT {s_idx+1}"
                
                with st.expander(titolo.upper()):
                    # Gestione Sistema
                    tipo = st.selectbox("Sistema", tipologie, key=f"sys_{user_sel}_{d_idx}_{s_idx}")
                    is_th = "Theory" in tipo
                    
                    def smart_select(label, cat, k_part):
                        opts = get_options(cat, is_th)
                        # Recupera il valore salvato o imposta a "-"
                        val = curr_vals.get(k_part, "-")
                        idx = opts.index(val) if val in opts else 0
                        res = st.selectbox(label, opts, index=idx, key=f"{k_part}_{user_sel}_{d_idx}_{s_idx}")
                        # Aggiorna il dizionario locale
                        deck["slots"][s_key][k_part] = res
                        return res

                    # Formazione Beyblade
                    if "BX/UX" in tipo and "+RIB" not in tipo:
                        smart_select("Blade", "blade", 'b')
                        smart_select("Ratchet", "ratchet", 'r')
                        smart_select("Bit", "bit", 'bi')
                    elif "CX" in tipo and "+RIB" not in tipo:
                        smart_select("Lock Bit", "lock_bit", 'lb')
                        smart_select("Main Blade", "main_blade", 'mb')
                        smart_select("Assist Blade", "assist_blade", 'ab')
                        smart_select("Ratchet", "ratchet", 'r')
                        smart_select("Bit", "bit", 'bi')
                    elif "+RIB" in tipo:
                        if "CX" in tipo:
                            smart_select("Lock Bit", "lock_bit", 'lb')
                            smart_select("Main Blade", "main_blade", 'mb')
                            smart_select("Assist Blade", "assist_blade", 'ab')
                        else: smart_select("Blade", "blade", 'b')
                        smart_select("RIB", "ratchet_integrated_bit", 'rib')

                    # Anteprime
                    cols = st.columns(5)
                    for i, (k, v) in enumerate(deck["slots"][s_key].items()):
                        if v != "-":
                            img_obj = get_img(global_img_map.get(v))
                            if img_obj: cols[i % 5].image(img_obj)

            # Azioni Deck
            if st.button(f"🗑️ Elimina {deck['name']}", key=f"del_{d_idx}"):
                user_data["decks"].pop(d_idx); save_cloud_manual(); st.rerun()

    if st.button("➕ Crea Nuovo Deck"):
        user_data["decks"].append({"name": f"DECK {len(user_data['decks'])+1}", "slots": {str(i): {} for i in range(3)}})
        save_cloud_manual(); st.rerun()