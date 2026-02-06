import streamlit as st
import pandas as pd
import hashlib
import os
import json
import requests
import base64
import time
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

def force_load():
    inv_c = github_action("inv", method="GET")
    deck_c = github_action("decks", method="GET")
    new_users = {}
    for u in ["Antonio", "Andrea", "Fabio"]:
        new_users[u] = {
            "inv": inv_c.get(u, {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}) if inv_c else {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]},
            "decks": deck_c.get(u, [{"name": "DECK 1", "slots": {"0":{}, "1":{}, "2":{}}}]) if deck_c else [{"name": "DECK 1", "slots": {"0":{}, "1":{}, "2":{}}}]
        }
    st.session_state.users = new_users

def save_cloud():
    inv_data = {u: d["inv"] for u, d in st.session_state.users.items()}
    deck_data = {u: d["decks"] for u, d in st.session_state.users.items()}
    if github_action("inv", inv_data, "PUT") and github_action("decks", deck_data, "PUT"):
        st.toast("✅ Dati salvati!", icon="💾")
    else: st.error("❌ Errore sincronizzazione")

# =========================
# INIZIALIZZAZIONE
# =========================
if 'users' not in st.session_state:
    force_load()

@st.dialog("Accesso Officina")
def user_dialog():
    for u in ["Antonio", "Andrea", "Fabio"]:
        if st.button(u, use_container_width=True):
            st.session_state.user_sel = u
            force_load()
            st.rerun()

if 'user_sel' not in st.session_state:
    user_dialog()
    st.stop()

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

df_db, global_img_map = load_db()
user_sel = st.session_state.user_sel
user_data = st.session_state.users[user_sel]

# Sidebar
st.sidebar.title(f"👤 {user_sel}")
if st.sidebar.button("🔄 Forza Aggiornamento Cloud"):
    force_load(); st.rerun()

if 'edit_name_idx' not in st.session_state: st.session_state.edit_name_idx = None

# =========================
# UI PRINCIPALE
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

# --- TAB 1: AGGIUNGI (INALTERATO) ---
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
                save_cloud()
            st.markdown("<hr>", unsafe_allow_html=True)
            for ck, ik in comps:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name-centered'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        user_data["inv"][ik][val] = user_data["inv"][ik].get(val, 0) + 1
                        save_cloud()

# --- TAB 2: INVENTARIO ---
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
                        save_cloud(); st.rerun()

# --- TAB 3: DECK BUILDER ---
with tab3:
    def get_options(cat, theory=False):
        if theory:
            csv_m = {"lock_bit": "lock_chip", "blade": "blade", "main_blade": "main_blade", "assist_blade": "assist_blade", "ratchet": "ratchet", "bit": "bit", "ratchet_integrated_bit": "ratchet_integrated_bit"}
            return ["-"] + sorted([x for x in df_db[csv_m.get(cat, cat)].unique().tolist() if x and x != "n/a"])
        return ["-"] + sorted(list(user_data["inv"][cat].keys()))
    
    tipologie = ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", "BX/UX Theory", "CX Theory", "BX/UX+RIB Theory", "CX+RIB Theory"]
    
    for d_idx, deck in enumerate(user_data["decks"]):
        # Definiamo quali chiavi appartengono a quale sistema per filtraggio
        sys_map = {
            "BX/UX": ["b", "r", "bi"],
            "CX": ["lb", "mb", "ab", "r", "bi"],
            "BX/UX+RIB": ["b", "rib"],
            "CX+RIB": ["lb", "mb", "ab", "rib"]
        }

        # Raccolta pezzi validi per duplicati (solo quelli del sistema attuale di ogni slot)
        all_active_parts = []
        for s in deck["slots"].values():
            s_type = s.get("_sys", "BX/UX").replace(" Theory", "")
            active_keys = sys_map.get(s_type, [])
            all_active_parts.extend([s.get(k) for k in active_keys if s.get(k) and s.get(k) != "-"])

        with st.expander(deck['name'].upper(), expanded=True):
            for s_idx in range(3):
                s_key = str(s_idx)
                if s_key not in deck["slots"]: deck["slots"][s_key] = {}
                curr = deck["slots"][s_key]
                
                # Tipo Corrente
                c_type = st.selectbox("Sistema", tipologie, key=f"t_{user_sel}_{d_idx}_{s_idx}", index=tipologie.index(curr.get("_sys", tipologie[0])))
                curr["_sys"] = c_type
                c_base_type = c_type.replace(" Theory", "")
                active_keys = sys_map.get(c_base_type, [])

                # Titolo Pulito (Solo pezzi attivi del sistema scelto)
                titolo_parti = [curr.get(k) for k in active_keys if curr.get(k) and curr.get(k) != "-"]
                avviso_slot = " ⚠️" if any(all_active_parts.count(p) > 1 for p in titolo_parti) else ""
                titolo_testo = " ".join(titolo_parti).strip() or f"SLOT {s_idx+1}"

                with st.expander(f"{titolo_testo.upper()}{avviso_slot}"):
                    is_th = "Theory" in c_type
                    
                    def update_comp(label, cat, k_comp):
                        opts = get_options(cat, is_th)
                        current_val = curr.get(k_comp, "-")
                        if current_val not in opts: current_val = "-"
                        
                        display_label = label
                        if current_val != "-" and all_active_parts.count(current_val) > 1:
                            display_label = f"{label} ⚠️"
                        
                        res = st.selectbox(display_label, opts, index=opts.index(current_val), key=f"sel_{k_comp}_{user_sel}_{d_idx}_{s_idx}")
                        if curr.get(k_comp) != res:
                            curr[k_comp] = res
                            # Rimosso st.rerun() per stabilità expander

                    # Mostra solo i widget necessari
                    if "BX/UX" in c_base_type and "+RIB" not in c_base_type:
                        update_comp("Blade", "blade", "b")
                        update_comp("Ratchet", "ratchet", "r")
                        update_comp("Bit", "bit", "bi")
                    elif "CX" in c_base_type and "+RIB" not in c_base_type:
                        update_comp("Lock Bit", "lock_bit", "lb")
                        update_comp("Main Blade", "main_blade", "mb")
                        update_comp("Assist Blade", "assist_blade", "ab")
                        update_comp("Ratchet", "ratchet", "r")
                        update_comp("Bit", "bit", "bi")
                    elif "+RIB" in c_base_type:
                        if "CX" in c_base_type:
                            update_comp("Lock Bit", "lock_bit", "lb")
                            update_comp("Main Blade", "main_blade", "mb")
                            update_comp("Assist Blade", "assist_blade", "ab")
                        else: update_comp("Blade", "blade", "b")
                        update_comp("RIB", "ratchet_integrated_bit", "rib")

                    # Anteprima Immagini FILTRATA (mostra solo ciò che appartiene al sistema)
                    cols = st.columns(5)
                    img_idx = 0
                    for k in active_keys:
                        v = curr.get(k)
                        if v and v != "-":
                            img_obj = get_img(global_img_map.get(v))
                            if img_obj:
                                cols[img_idx % 5].image(img_obj)
                                img_idx += 1

            # Pulsanti Deck
            c1, c2, c3, _ = st.columns([0.2, 0.2, 0.2, 0.4])
            if c1.button("Rinomina", key=f"r_{user_sel}_{d_idx}"):
                st.session_state.edit_name_idx = f"{user_sel}_{d_idx}"; st.rerun()
            if c2.button("Salva Deck", key=f"s_{user_sel}_{d_idx}"):
                save_cloud()
            if c3.button("Elimina", key=f"e_{user_sel}_{d_idx}", type="primary"):
                user_data["decks"].pop(d_idx); save_cloud(); st.rerun()
            
            if st.session_state.edit_name_idx == f"{user_sel}_{d_idx}":
                n_name = st.text_input("Nuovo nome:", deck['name'], key=f"i_{d_idx}")
                if st.button("OK", key=f"o_{d_idx}"):
                    deck['name'] = n_name; st.session_state.edit_name_idx = None; save_cloud(); st.rerun()

    if st.button("Nuovo Deck"):
        user_data["decks"].append({"name": f"DECK {len(user_data['decks'])+1}", "slots": {"0":{}, "1":{}, "2":{}}})
        save_cloud(); st.rerun()