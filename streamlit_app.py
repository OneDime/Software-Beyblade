import streamlit as st
import pandas as pd
import hashlib
import os
import json
import requests
import base64
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE (INALTERATO)
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
    div.stButton > button { width: auto !important; min-width: 150px !important; height: 30px !important; background-color: #334155 !important; color: white !important; border: 1px solid #475569 !important; border-radius: 4px !important; }
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; text-align: left !important; margin-bottom: 5px !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# LOGICA GITHUB
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
            requests.put(url, headers=headers, json=payload)
    except Exception as e:
        st.error(f"GitHub Error: {e}")
    return None

def save_cloud():
    inv_data = {u: d["inv"] for u, d in st.session_state.users.items()}
    deck_data = {u: d["decks"] for u, d in st.session_state.users.items()}
    github_action("inv", inv_data, "PUT")
    github_action("decks", deck_data, "PUT")
    st.sidebar.success("Sincronizzato!")

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
# LOGICA DATI & IMMAGINI
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
    if cloud: st.session_state.users = cloud
    else:
        st.session_state.users = {u: {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {str(i): {} for i in range(3)}}]} for u in ["Antonio", "Andrea", "Fabio"]}

# --- PUNTO 1: CONFIGURAZIONE URL ---
user_list = ["Antonio", "Andrea", "Fabio"]
q_params = st.query_params
initial_user = q_params.get("user", "Antonio")
if initial_user not in user_list: initial_user = "Antonio"

st.sidebar.title("👤 Account")
user_sel = st.sidebar.radio("Seleziona Utente:", user_list, index=user_list.index(initial_user))

if user_sel != initial_user:
    st.query_params["user"] = user_sel
    st.rerun()

user_data = st.session_state.users[user_sel]
if 'exp_state' not in st.session_state: st.session_state.exp_state = {}
if 'edit_name_idx' not in st.session_state: st.session_state.edit_name_idx = None
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
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"),
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"),
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                for ck, ik in comps:
                    val = row[ck]
                    if val and val != "n/a": user_data["inv"][ik][val] = user_data["inv"][ik].get(val, 0) + 1
                save_cloud(); st.toast("Aggiunto!")
            st.markdown("<hr>", unsafe_allow_html=True)
            for ck, ik in comps:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name-centered'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        user_data["inv"][ik][val] = user_data["inv"][ik].get(val, 0) + 1
                        save_cloud(); st.toast(f"Aggiunto: {val}")

with tab2:
    modo = st.radio("Azione", ["Aggiungi (+1)", "Rimuovi (-1)"], horizontal=True, label_visibility="collapsed")
    op = 1 if "Aggiungi" in modo else -1
    for cat, items in user_data["inv"].items():
        if items:
            with st.expander(cat.replace('_', ' ').upper()):
                for n, q in list(items.items()):
                    if st.button(f"{n} x{q}", key=f"inv_{user_sel}_{cat}_{n}"):
                        user_data["inv"][cat][n] += op
                        if user_data["inv"][cat][n] <= 0: del user_data["inv"][cat][n]
                        save_cloud(); st.rerun()

with tab3:
    def get_options(cat, theory=False):
        if theory:
            csv_m = {"lock_bit": "lock_chip", "blade": "blade", "main_blade": "main_blade", "assist_blade": "assist_blade", "ratchet": "ratchet", "bit": "bit", "ratchet_integrated_bit": "ratchet_integrated_bit"}
            return ["-"] + sorted([x for x in df_db[csv_m.get(cat, cat)].unique().tolist() if x and x != "n/a"])
        return ["-"] + sorted(list(user_data["inv"][cat].keys()))
    
    tipologie = ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", "BX/UX Theory", "CX Theory", "BX/UX+RIB Theory", "CX+RIB Theory"]
    for d_idx, deck in enumerate(user_data["decks"]):
        with st.expander(f"{deck['name'].upper()}", expanded=True):
            for s_idx in range(3):
                s_key = str(s_idx)
                sels = deck["slots"].get(s_key, {})
                titolo = " ".join([v for v in sels.values() if v and v != "-"]) or f"SLOT {s_idx+1}"
                exp_key = f"{user_sel}-{d_idx}-{s_idx}"
                
                with st.expander(titolo.upper(), expanded=st.session_state.exp_state.get(exp_key, False)):
                    # --- PUNTO 2: SALVATAGGIO FORZATO CON on_change ---
                    tipo = st.selectbox("Sistema", tipologie, key=f"ty_{exp_key}", on_change=save_cloud)
                    is_th, curr = "Theory" in tipo, {}
                    
                    if "BX/UX" in tipo and "+RIB" not in tipo:
                        curr['b'] = st.selectbox("Blade", get_options("blade", is_th), key=f"b_{exp_key}", on_change=save_cloud)
                        curr['r'] = st.selectbox("Ratchet", get_options("ratchet", is_th), key=f"r_{exp_key}", on_change=save_cloud)
                        curr['bi'] = st.selectbox("Bit", get_options("bit", is_th), key=f"bi_{exp_key}", on_change=save_cloud)
                    elif "CX" in tipo and "+RIB" not in tipo:
                        curr['lb'] = st.selectbox("Lock Bit", get_options("lock_bit", is_th), key=f"lb_{exp_key}", on_change=save_cloud)
                        curr['mb'] = st.selectbox("Main Blade", get_options("main_blade", is_th), key=f"mb_{exp_key}", on_change=save_cloud)
                        curr['ab'] = st.selectbox("Assist Blade", get_options("assist_blade", is_th), key=f"ab_{exp_key}", on_change=save_cloud)
                        curr['r'] = st.selectbox("Ratchet", get_options("ratchet", is_th), key=f"r_{exp_key}", on_change=save_cloud)
                        curr['bi'] = st.selectbox("Bit", get_options("bit", is_th), key=f"bi_{exp_key}", on_change=save_cloud)
                    elif "+RIB" in tipo:
                        if "CX" in tipo:
                            curr['lb'] = st.selectbox("Lock Bit", get_options("lock_bit", is_th), key=f"lb_{exp_key}", on_change=save_cloud)
                            curr['mb'] = st.selectbox("Main Blade", get_options("main_blade", is_th), key=f"mb_{exp_key}", on_change=save_cloud)
                            curr['ab'] = st.selectbox("Assist Blade", get_options("assist_blade", is_th), key=f"ab_{exp_key}", on_change=save_cloud)
                        else: curr['b'] = st.selectbox("Blade", get_options("blade", is_th), key=f"b_{exp_key}", on_change=save_cloud)
                        curr['rib'] = st.selectbox("RIB", get_options("ratchet_integrated_bit", is_th), key=f"rib_{exp_key}", on_change=save_cloud)
                    
                    cols = st.columns(5)
                    for idx, (k, v) in enumerate(curr.items()):
                        if v != "-":
                            img_obj = get_img(global_img_map.get(v))
                            if img_obj: cols[idx].image(img_obj)
                    
                    if deck["slots"].get(s_key) != curr:
                        deck["slots"][s_key] = curr
                        st.session_state.exp_state[exp_key] = True
                        st.rerun()

            c1, c2, _ = st.columns([0.2, 0.2, 0.6])
            if c1.button("📝 Rinomina", key=f"ren_{user_sel}_{d_idx}"): st.session_state.edit_name_idx = f"{user_sel}_{d_idx}"; st.rerun()
            if c2.button("🗑️ Elimina", key=f"del_{user_sel}_{d_idx}", type="primary"): user_data["decks"].pop(d_idx); save_cloud(); st.rerun()
            if st.session_state.edit_name_idx == f"{user_sel}_{d_idx}":
                n_name = st.text_input("Nuovo nome:", deck['name'], key=f"edit_input_{d_idx}")
                if st.button("Conferma", key=f"confirm_{d_idx}"):
                    deck['name'] = n_name; st.session_state.edit_name_idx = None; save_cloud(); st.rerun()

    if st.button("➕ Nuovo Deck"): user_data["decks"].append({"name": f"DECK {len(user_data['decks'])+1}", "slots": {str(i): {} for i in range(3)}}); save_cloud(); st.rerun()