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

# =========================
# CONFIGURAZIONE & STILE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    :root { color-scheme: dark; }
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    .user-title { font-size: 28px !important; font-weight: bold; margin-bottom: 20px; color: #f1f5f9; text-align: center; width: 100%; }
    
    .add-tab-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        width: 100%;
    }

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
        background-color: #0f172a;
        border-left: 4px solid #60a5fa;
        padding: 8px 12px;
        margin: 4px 0px;
        border-radius: 4px;
        text-align: left;
        width: 100%;
    }
    .slot-summary-name { font-weight: bold; color: #f1f5f9; text-transform: uppercase; }
    .slot-summary-alert { color: #fbbf24; font-weight: bold; margin-left: 8px; font-size: 0.85rem; }
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
            "decks": deck_c.get(u, [{"name": "DECK 1", "slots": {"0":{"tipo":"BX/UX"}, "1":{"tipo":"BX/UX"}, "2":{"tipo":"BX/UX"}}}]) if deck_c else [{"name": "DECK 1", "slots": {"0":{"tipo":"BX/UX"}, "1":{"tipo":"BX/UX"}, "2":{"tipo":"BX/UX"}}}]
        }
    st.session_state.users = new_users

def save_cloud():
    inv_data = {u: d["inv"] for u, d in st.session_state.users.items()}
    deck_data = {u: d["decks"] for u, d in st.session_state.users.items()}
    
    ok1 = github_action("inv", inv_data, "PUT")
    ok2 = github_action("decks", deck_data, "PUT")
    
    if ok1 and ok2:
        st.toast("✅ Dati salvati!", icon="💾")
    else: st.error("❌ Errore sincronizzazione")

if 'users' not in st.session_state:
    force_load()

# =========================
# GESTIONE LOGIN PERSISTENTE
# =========================
valid_users = ["Antonio", "Andrea", "Fabio"]

query_params = st.query_params
url_user = query_params.get("user")

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
                force_load()
                st.rerun()
    
    user_dialog()
    st.stop()

# =========================
# CARICAMENTO DATABASE
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

# Sidebar
st.sidebar.title(f"👤 {st.session_state.user_sel}")

if st.sidebar.button("Esci / Cambia Utente"):
    st.query_params.clear()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

if st.sidebar.button("🔄 Forza Sync Cloud"):
    force_load()
    st.rerun()

if st.sidebar.button("📂 Aggiorna Database CSV"):
    st.cache_data.clear()
    st.toast("Database ricaricato!", icon="📂")
    time.sleep(1)
    st.rerun()

df_db, global_img_map = load_db()
user_sel = st.session_state.user_sel
user_data = st.session_state.users[user_sel]

if 'edit_name_idx' not in st.session_state: st.session_state.edit_name_idx = None

tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

# --- TAB 1: AGGIUNGI ---
with tab1:
    search_q = st.text_input("Cerca Beyblade...", "").lower()
    filtered = df_db[df_db['_search'].str.contains(search_q)] if search_q else df_db.head(10)
    
    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.expander(f"**{row['name'].upper()}**", expanded=False):
            with st.container(border=True):
                img = get_img(row['blade_image'] or row['beyblade_page_image'], size=(150, 150))
                if img: 
                    st.image(img)
                
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
                for n in sorted(list(items.keys())):
                    q = items[n]
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
        all_selected = []
        for s in deck["slots"].values():
            all_selected.extend([v for k, v in s.items() if v and v != "-" and k != "tipo"])

        with st.expander(deck['name'].upper(), expanded=True):
            for s_idx in range(3):
                curr = deck["slots"].get(str(s_idx), {})
                
                # --- FIX ORDINAMENTO NOMI ---
                # Recuperiamo il tipo del sistema corrente (default BX/UX)
                tipo_sys = curr.get("tipo", "BX/UX")
                
                # Definiamo l'ordine esatto delle chiavi in base al sistema scelto
                keys_order = []
                if "CX" in tipo_sys:
                    if "+RIB" in tipo_sys:
                        keys_order = ["lb", "mb", "ab", "rib"] # CX + RIB: Lock -> Main -> Assist -> RIB
                    else:
                        keys_order = ["lb", "mb", "ab", "r", "bi"] # CX Standard: Lock -> Main -> Assist -> Ratchet -> Bit
                else:
                    # BX/UX
                    if "+RIB" in tipo_sys:
                        keys_order = ["b", "rib"] # BX + RIB
                    else:
                        keys_order = ["b", "r", "bi"] # BX Standard
                
                # Costruiamo il titolo seguendo RIGOROSAMENTE l'ordine definito sopra
                titolo_base = []
                for k in keys_order:
                    val = curr.get(k)
                    if val and val != "-":
                        titolo_base.append(val)
                # -----------------------------
                
                nome_bey = " ".join(titolo_base).strip() or f"Slot {s_idx+1} Vuoto"
                ha_duplicati = any(all_selected.count(p) > 1 for p in titolo_base)
                alert_html = "<span class='slot-summary-alert'>⚠️ DUPLICATO</span>" if ha_duplicati else ""
                st.markdown(f"<div class='slot-summary-box'><span class='slot-summary-name'>{nome_bey}</span>{alert_html}</div>", unsafe_allow_html=True)
            
            st.markdown("<hr>", unsafe_allow_html=True)

            for s_idx in range(3):
                s_key = str(s_idx)
                if s_key not in deck["slots"]: deck["slots"][s_key] = {"tipo": "BX/UX"}
                curr = deck["slots"][s_key]
                
                with st.expander(f"SLOT {s_idx+1}"):
                    old_tipo = curr.get("tipo", "BX/UX")
                    tipo = st.selectbox("Sistema", tipologie, index=tipologie.index(old_tipo), key=f"t_{user_sel}_{d_idx}_{s_idx}")
                    
                    if tipo != old_tipo:
                        valid_keys = ["tipo"]
                        if "BX/UX" in tipo and "+RIB" not in tipo: valid_keys += ["b", "r", "bi"]
                        elif "CX" in tipo and "+RIB" not in tipo: valid_keys += ["lb", "mb", "ab", "r", "bi"]
                        elif "+RIB" in tipo:
                            if "CX" in tipo: valid_keys += ["lb", "mb", "ab", "rib"]
                            else: valid_keys += ["b", "rib"]
                        
                        for k in ["b", "r", "bi", "lb", "mb", "ab", "rib"]:
                            if k not in valid_keys: curr[k] = "-"
                        curr["tipo"] = tipo
                        st.rerun()

                    is_th = "Theory" in tipo
                    
                    def update_comp(label, cat, k_comp):
                        opts = get_options(cat, is_th)
                        current_val = curr.get(k_comp, "-")
                        if current_val not in opts: current_val = "-"
                        display_label = f"{label} ⚠️" if current_val != "-" and all_selected.count(current_val) > 1 else label
                        res = st.selectbox(display_label, opts, index=opts.index(current_val), key=f"sel_{k_comp}_{user_sel}_{d_idx}_{s_idx}")
                        if curr.get(k_comp) != res:
                            curr[k_comp] = res
                            st.rerun()

                    if "BX/UX" in tipo and "+RIB" not in tipo:
                        update_comp("Blade", "blade", "b"); update_comp("Ratchet", "ratchet", "r"); update_comp("Bit", "bit", "bi")
                    elif "CX" in tipo and "+RIB" not in tipo:
                        update_comp("Lock Bit", "lock_bit", "lb"); update_comp("Main Blade", "main_blade", "mb"); update_comp("Assist Blade", "assist_blade", "ab"); update_comp("Ratchet", "ratchet", "r"); update_comp("Bit", "bit", "bi")
                    elif "+RIB" in tipo:
                        if "CX" in tipo:
                            update_comp("Lock Bit", "lock_bit", "lb"); update_comp("Main Blade", "main_blade", "mb"); update_comp("Assist Blade", "assist_blade", "ab")
                        else: update_comp("Blade", "blade", "b")
                        update_comp("RIB", "ratchet_integrated_bit", "rib")

                    cols = st.columns(5)
                    for k, v in curr.items():
                        if k != "tipo" and v and v != "-":
                            img_obj = get_img(global_img_map.get(v))
                            if img_obj: st.image(img_obj, width=80)

            c1, c2, c3, _ = st.columns([0.2, 0.2, 0.2, 0.4])
            if c1.button("Rinomina", key=f"r_{user_sel}_{d_idx}"):
                st.session_state.edit_name_idx = f"{user_sel}_{d_idx}"; st.rerun()
            if c2.button("Salva Deck", key=f"s_{user_sel}_{d_idx}"): save_cloud()
            if c3.button("Elimina", key=f"e_{user_sel}_{d_idx}", type="primary"):
                user_data["decks"].pop(d_idx); save_cloud(); st.rerun()
            if st.session_state.edit_name_idx == f"{user_sel}_{d_idx}":
                n_name = st.text_input("Nuovo nome:", deck['name'], key=f"i_{d_idx}")
                if st.button("OK", key=f"o_{d_idx}"):
                    deck['name'] = n_name; st.session_state.edit_name_idx = None; save_cloud(); st.rerun()

    if st.button("Nuovo Deck"):
        user_data["decks"].append({"name": f"DECK {len(user_data['decks'])+1}", "slots": {"0":{"tipo":"BX/UX"}, "1":{"tipo":"BX/UX"}, "2":{"tipo":"BX/UX"}}})
        save_cloud(); st.rerun()