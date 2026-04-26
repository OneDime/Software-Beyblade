import streamlit as st
import pandas as pd
import hashlib
import os
import json
import requests
import base64
import time
import re
import io
from datetime import datetime, timedelta
from PIL import Image
import google.generativeai as genai

# =========================
# CONFIGURAZIONE & STILE
# =========================
def inject_css():
    st.markdown("""
        <style>
        :root { color-scheme: dark; }
        .stApp { background-color: #0f172a; color: #f1f5f9; }
        
        /* Forza grigio scuro su barre di ricerca e input (fisso anche su mobile) */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            background-color: #1e293b !important;
            color: #f1f5f9 !important;
            border: 1px solid #334155 !important;
        }

        /* Forza stile scuro sulla Tabella / Data Editor */
        [data-testid="stDataEditor"], [data-testid="stDataFrame"], .stTable {
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
        }

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
            padding: 25px; border-radius: 12px; color: #f1f5f9;
            line-height: 1.7; text-align: left !important; white-space: pre-wrap;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        </style>
        """, unsafe_allow_html=True)

# Impostazione Icona
st.set_page_config(
    page_title="Officina Beyblade X", 
    page_icon="icona.png", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

inject_css()

# =========================
# LOGICA GITHUB E MIGRAZIONE DATI
# =========================
GITHUB_TOKEN = st.secrets["github_token"]
REPO = st.secrets["github_repo"]
FILES = {"inv": "inventario.json", "decks": "decks.json", "stats": "match_stats.json"}

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
            return [] if file_key == "stats" else None
        elif method == "PUT":
            payload = {
                "message": f"App Update {FILES[file_key]}", 
                "content": base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8'), 
                "sha": sha
            }
            return requests.put(url, headers=headers, json=payload).status_code in [200, 201]
    except Exception as e:
        print(f"Errore API GitHub: {e}")
        return False
    return False

def force_load():
    inv_c = github_action("inv", method="GET")
    deck_c = github_action("decks", method="GET")
    new_users = {}
    
    req_keys = ["lock_chip", "blade", "over_blade", "metal_blade", "main_blade", "assist_blade", "r_i_blade", "ratchet", "bit", "r_i_bit"]
    
    for u in ["Antonio", "Andrea", "Fabio"]:
        user_inv = inv_c.get(u, {}) if inv_c else {}
        
        for k in req_keys:
            if k not in user_inv:
                user_inv[k] = {}
                
        if "lock_bit" in user_inv:
            user_inv["lock_chip"].update(user_inv.pop("lock_bit"))
        if "ratchet_integrated_bit" in user_inv:
            user_inv["r_i_bit"].update(user_inv.pop("ratchet_integrated_bit"))
        if "ratchet_integrated_blade" in user_inv:
            user_inv["r_i_blade"].update(user_inv.pop("ratchet_integrated_blade"))
            
        raw_decks = deck_c.get(u, [])
        if isinstance(raw_decks, list):
            beys_list = []
            deck_list = []
            for d in raw_decks:
                new_deck = {"name": d.get("name", "DECK"), "slots": {}}
                for s_idx, s_data in d.get("slots", {}).items():
                    if isinstance(s_data, dict) and s_data.get("tipo"):
                        bey_id = hashlib.md5(f"{u}_{d.get('name')}_{s_idx}_{time.time()}".encode()).hexdigest()[:8]
                        s_data["id"] = bey_id
                        beys_list.append(s_data)
                        new_deck["slots"][str(s_idx)] = bey_id
                    else:
                        new_deck["slots"][str(s_idx)] = "-"
                deck_list.append(new_deck)
            if not deck_list:
                deck_list.append({"name": "DECK 1", "slots": {"0":"-", "1":"-", "2":"-"}})
            decks_obj = {"beys": beys_list, "deck_list": deck_list}
        else:
            decks_obj = raw_decks
            
        new_users[u] = {
            "inv": user_inv,
            "decks": decks_obj
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

# =========================
# LOGIN PERSISTENTE
# =========================
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

# =========================
# DATABASE E CACHE
# =========================
@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame(), {}, {}
    df = pd.read_csv("beyblade_x.csv").fillna("")
    img_map = {}
    theory_opts = {}
    mapping = [('lock_chip', 'lock_chip_image', 'lock_chip'), 
               ('blade', 'blade_image', 'blade'), 
               ('over_blade', 'over_blade_image', 'over_blade'), 
               ('metal_blade', 'metal_blade_image', 'metal_blade'), 
               ('main_blade', 'main_blade_image', 'main_blade'), 
               ('assist_blade', 'assist_blade_image', 'assist_blade'), 
               ('ratchet_integrated_blade', 'ratchet_integrated_blade_image', 'r_i_blade'),
               ('ratchet', 'ratchet_image', 'ratchet'), 
               ('bit', 'bit_image', 'bit'), 
               ('ratchet_integrated_bit', 'ratchet_integrated_bit_image', 'r_i_bit')]
    
    for _, _, state_key in mapping:
        theory_opts[state_key] = ["-"]

    for csv_col, img_col, state_key in mapping:
        if csv_col in df.columns:
            theory_opts[state_key] = ["-"] + sorted([x for x in df[csv_col].unique().tolist() if x and x != "n/a"])
    
    for _, r in df.iterrows():
        for c_col, i_col, _ in mapping:
            if c_col in df.columns and i_col in df.columns:
                val, img = str(r[c_col]), str(r[i_col])
                if val and val != "n/a" and img and img != "n/a":
                    img_map[val] = img

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

def get_bey_name_and_comps(curr):
    t_sys = curr.get("tipo", "BX/UX")
    if "CX Infinity" in t_sys:
        k_order = ["lc", "ob", "meb", "ab", "rib"] if "+R-I-Bit" in t_sys else ["lc", "ob", "meb", "ab", "r", "bi"]
    elif "CX" in t_sys:
        k_order = ["lc", "mb", "ab", "rib"] if "+R-I-Bit" in t_sys else ["lc", "mb", "ab", "r", "bi"]
    elif "R-I-Blade" in t_sys:
        k_order = ["ribl", "bi"]
    else:
        k_order = ["b", "rib"] if "+R-I-Bit" in t_sys else ["b", "r", "bi"]
    
    parts = [curr.get(k) for k in k_order if curr.get(k) and curr.get(k) != "-"]
    nome_bey = " ".join(parts).strip() or "Nuovo Beyblade"
    return nome_bey, parts, k_order

df_db, global_img_map, theory_opts = load_db()
user_sel = st.session_state.user_sel
user_data = st.session_state.users[user_sel]

if 'edit_name_idx' not in st.session_state: st.session_state.edit_name_idx = None

# Sidebar
st.sidebar.title(f"👤 {user_sel}")
if st.sidebar.button("Esci / Cambia Utente"):
    st.query_params.clear()
    for key in list(st.session_state.keys()): 
        del st.session_state[key]
    st.rerun()

# =========================
# MENU DI NAVIGAZIONE
# =========================
menu_scelta = st.selectbox("🧭 Menu di Navigazione", ["Inventario", "Builder", "Match!", "Meta"])

if menu_scelta == "Inventario":
    tab1, tab2 = st.tabs(["🔍 Aggiungi", "📦 Inventario"])

    # --- TAB 1: AGGIUNGI ---
    with tab1:
        search_q = st.text_input("Cerca Beyblade...", "").lower()
        filtered = df_db[df_db['_search'].str.contains(search_q)] if search_q else df_db.head(10)
        for i, (_, row) in enumerate(filtered.iterrows()):
            with st.expander(f"**{row['name'].upper()}**"):
                with st.container(border=True):
                    img = get_img(row['blade_image'] or row['beyblade_page_image'], size=(150, 150))
                    if img: st.image(img)
                    comps = [("lock_chip", "lock_chip"), ("blade", "blade"), 
                             ("over_blade", "over_blade"), ("metal_blade", "metal_blade"), 
                             ("main_blade", "main_blade"), ("assist_blade", "assist_blade"), 
                             ("ratchet_integrated_blade", "r_i_blade"), 
                             ("ratchet", "ratchet"), ("bit", "bit"), 
                             ("ratchet_integrated_bit", "r_i_bit")]
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
        order = ["lock_chip", "blade", "over_blade", "metal_blade", "main_blade", "assist_blade", "r_i_blade", "ratchet", "bit", "r_i_bit"]
        display_names = {
            "lock_chip": "LOCK CHIP", "blade": "BLADE", "over_blade": "OVER BLADE", 
            "metal_blade": "METAL BLADE", "main_blade": "MAIN BLADE", "assist_blade": "ASSIST BLADE", 
            "r_i_blade": "RATCHET-INTEGRATED-BLADE", "ratchet": "RATCHET", "bit": "BIT", "r_i_bit": "RATCHET-INTEGRATED-BIT"
        }
        for cat in order:
            items = user_data["inv"].get(cat, {})
            if items:
                with st.expander(display_names[cat]):
                    for n in sorted(list(items.keys())):
                        if st.button(f"{n} x{items[n]}", key=f"inv_{user_sel}_{cat}_{n}"):
                            user_data["inv"][cat][n] += op
                            if user_data["inv"][cat][n] <= 0: del user_data["inv"][cat][n]
                            save_cloud(); st.rerun()

elif menu_scelta == "Builder":
    tab_bey, tab_deck = st.tabs(["🧩 Beyblade Builder", "🃏 Deck Builder"])

# --- BEYBLADE BUILDER ---
    with tab_bey:
        if st.button("➕ Crea Beyblade", type="primary"):
            new_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
            user_data["decks"]["beys"].append({"id": new_id, "tipo": "BX/UX", "is_new": True})
            st.session_state.last_edited_bey = new_id
            save_cloud(); st.rerun()
            
        search_bey = st.text_input("Cerca Beyblade...", "").lower()
            
        inv_opts = {cat: (["-"] + sorted(list(items.keys()))) for cat, items in user_data["inv"].items()}
        tipologie = ["BX/UX", "BX/UX+R-I-Bit", "CX", "CX+R-I-Bit", "CX Infinity", "CX Infinity+R-I-Bit", "R-I-Blade+Bit", "BX/UX Theory", "BX/UX+R-I-Bit Theory", "CX Theory", "CX+R-I-Bit Theory", "CX Infinity Theory", "CX Infinity+R-I-Bit Theory", "R-I-Blade+Bit Theory"]
        
        def bey_sort_key(b):
            nome, _, _ = get_bey_name_and_comps(b)
            # Aggiunta (Theory) alla chiave di ordinamento se il sistema lo prevede
            if "Theory" in b.get("tipo", ""):
                nome += " (Theory)"
            is_new = 0 if b.get("is_new") else 1
            return (is_new, nome.lower())
            
        user_data["decks"]["beys"].sort(key=bey_sort_key)
        
        for b_idx, bey in enumerate(user_data["decks"]["beys"]):
            nome_bey, _, _ = get_bey_name_and_comps(bey)
            
            # Aggiunta automatica (Theory) al nome visualizzato se il sistema contiene "Theory"
            if "Theory" in bey.get("tipo", ""):
                nome_bey += " (Theory)"
            
            if search_bey and search_bey not in nome_bey.lower():
                continue
                
            is_expanded = (st.session_state.get("last_edited_bey") == bey["id"])
            
            with st.expander(nome_bey.upper(), expanded=is_expanded):
                tipo = st.selectbox("Sistema", tipologie, index=tipologie.index(bey.get("tipo", "BX/UX")), key=f"tb_sys_{bey['id']}")
                if tipo != bey.get("tipo"):
                    bey["tipo"] = tipo
                    st.session_state.last_edited_bey = bey["id"]
                    st.rerun()

                is_th = "Theory" in tipo
                def update_comp_bey(label, cat, k_comp):
                    opts = theory_opts.get(cat, ["-"]) if is_th else inv_opts.get(cat, ["-"])
                    val = bey.get(k_comp, "-")
                    if val not in opts: val = "-"
                    res = st.selectbox(label, opts, index=opts.index(val), key=f"sel_{k_comp}_{bey['id']}")
                    if bey.get(k_comp) != res:
                        bey[k_comp] = res
                        st.session_state.last_edited_bey = bey["id"]
                        st.rerun()

                if "CX Infinity" in tipo:
                    update_comp_bey("Lock Chip", "lock_chip", "lc")
                    update_comp_bey("Over Blade", "over_blade", "ob")
                    update_comp_bey("Metal Blade", "metal_blade", "meb")
                    update_comp_bey("Assist Blade", "assist_blade", "ab")
                    if "+R-I-Bit" in tipo:
                        update_comp_bey("R-I-Bit", "r_i_bit", "rib")
                        k_imgs = ["lc", "ob", "meb", "ab", "rib"]
                    else:
                        update_comp_bey("Ratchet", "ratchet", "r")
                        update_comp_bey("Bit", "bit", "bi")
                        k_imgs = ["lc", "ob", "meb", "ab", "r", "bi"]
                
                elif "CX" in tipo:
                    update_comp_bey("Lock Chip", "lock_chip", "lc")
                    update_comp_bey("Main Blade", "main_blade", "mb")
                    update_comp_bey("Assist Blade", "assist_blade", "ab")
                    if "+R-I-Bit" in tipo:
                        update_comp_bey("R-I-Bit", "r_i_bit", "rib")
                        k_imgs = ["lc", "mb", "ab", "rib"]
                    else:
                        update_comp_bey("Ratchet", "ratchet", "r")
                        update_comp_bey("Bit", "bit", "bi")
                        k_imgs = ["lc", "mb", "ab", "r", "bi"]
                
                elif "R-I-Blade" in tipo:
                    update_comp_bey("R-I-Blade", "r_i_blade", "ribl")
                    update_comp_bey("Bit", "bit", "bi")
                    k_imgs = ["ribl", "bi"]
                else:
                    update_comp_bey("Blade", "blade", "b")
                    if "+R-I-Bit" in tipo:
                        update_comp_bey("R-I-Bit", "r_i_bit", "rib")
                        k_imgs = ["b", "rib"]
                    else:
                        update_comp_bey("Ratchet", "ratchet", "r")
                        update_comp_bey("Bit", "bit", "bi")
                        k_imgs = ["b", "r", "bi"]

                st.write("") 
                cols = st.columns(len(k_imgs) if len(k_imgs) > 0 else 1)
                col_idx = 0
                for k in k_imgs:
                    v = bey.get(k)
                    if v and v != "-":
                        img_map_val = global_img_map.get(v)
                        img_obj = get_img(img_map_val)
                        if img_obj: cols[col_idx].image(img_obj, width=80); col_idx += 1
                        
                st.markdown("<hr>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                if c1.button("Salva", key=f"sv_bey_{bey['id']}"):
                    if "is_new" in bey:
                        del bey["is_new"]
                    st.session_state.last_edited_bey = None
                    save_cloud(); st.success("Salvato!")
                    st.rerun()
                if c2.button("Elimina", key=f"rm_bey_{bey['id']}", type="primary"):
                    b_id_to_rem = bey["id"]
                    user_data["decks"]["beys"].pop(b_idx)
                    for d in user_data["decks"]["deck_list"]:
                        for s_k, s_v in d["slots"].items():
                            if s_v == b_id_to_rem: d["slots"][s_k] = "-"
                    save_cloud(); st.rerun()


    # --- DECK BUILDER ---
    with tab_deck:
        bey_options = {"-": "- Nessuno -"}
        for b in user_data["decks"]["beys"]:
            n, _, _ = get_bey_name_and_comps(b)
            bey_options[b["id"]] = n
            
        bey_list_display = ["-"] + [b["id"] for b in user_data["decks"]["beys"]]
        
        def format_bey_opt(b_id):
            return bey_options.get(b_id, "-")
            
        for d_idx, deck in enumerate(user_data["decks"]["deck_list"]):
            all_deck_comps = []
            slot_names = []
            
            for s_idx in range(3):
                b_id = deck["slots"].get(str(s_idx), "-")
                if b_id != "-" and b_id in bey_options:
                    bey = next((x for x in user_data["decks"]["beys"] if x["id"] == b_id), None)
                    if bey:
                        n, parts, _ = get_bey_name_and_comps(bey)
                        all_deck_comps.extend(parts)
                        slot_names.append(n)
                    else:
                        slot_names.append(f"Slot {s_idx+1} Vuoto")
                else:
                    slot_names.append(f"Slot {s_idx+1} Vuoto")

            with st.expander(deck['name'].upper(), expanded=False):
                for s_idx in range(3):
                    b_id = deck["slots"].get(str(s_idx), "-")
                    ha_duplicati = False
                    if b_id != "-" and b_id in bey_options:
                        bey = next((x for x in user_data["decks"]["beys"] if x["id"] == b_id), None)
                        if bey:
                            _, parts, _ = get_bey_name_and_comps(bey)
                            if any(all_deck_comps.count(p) > 1 for p in parts):
                                ha_duplicati = True
                    
                    alert = f"<span class='slot-summary-alert'>⚠️ DUPLICATO</span>" if ha_duplicati else ""
                    st.markdown(f"<div class='slot-summary-box'><span class='slot-summary-name'>{slot_names[s_idx]}</span>{alert}</div>", unsafe_allow_html=True)
                
                st.markdown("<hr>", unsafe_allow_html=True)
                
                for s_idx in range(3):
                    s_key = str(s_idx)
                    curr_val = deck["slots"].get(s_key, "-")
                    if curr_val not in bey_list_display: curr_val = "-"
                    
                    new_val = st.selectbox(f"Slot {s_idx+1}", bey_list_display, format_func=format_bey_opt, index=bey_list_display.index(curr_val), key=f"sel_dkbey_{d_idx}_{s_idx}")
                    if new_val != curr_val:
                        deck["slots"][s_key] = new_val; st.rerun()
                
                st.write("")
                c1, c2, c3, _ = st.columns([0.2, 0.2, 0.2, 0.4])
                if c1.button("Rinomina", key=f"ren_d_{d_idx}"):
                    st.session_state.edit_name_idx = f"deck_{d_idx}"; st.rerun()
                if c2.button("Salva Deck", key=f"sav_d_{d_idx}"): 
                    save_cloud(); st.success("Salvato!")
                if c3.button("Elimina", key=f"del_d_{d_idx}", type="primary"):
                    user_data["decks"]["deck_list"].pop(d_idx); save_cloud(); st.rerun()
                
                if st.session_state.edit_name_idx == f"deck_{d_idx}":
                    n_name = st.text_input("Nuovo nome:", deck['name'], key=f"inp_ren_{d_idx}")
                    if st.button("OK", key=f"ok_ren_{d_idx}"):
                        deck['name'] = n_name; st.session_state.edit_name_idx = None; save_cloud(); st.rerun()
                        
        if st.button("➕ Nuovo Deck", type="primary"):
            user_data["decks"]["deck_list"].append({"name": f"DECK {len(user_data['decks']['deck_list'])+1}", "slots": {"0":"-", "1":"-", "2":"-"}})
            save_cloud(); st.rerun()

elif menu_scelta == "Match!":
    tab5, tab6 = st.tabs(["📊 Registro Match", "🏆 Classifica Beyblade"])

# --- TAB 5: REGISTRO MATCH ---
    with tab5:
        st.markdown("### 📊 Registro Rapido Scontri")
        
        if 'match_counter' not in st.session_state:
            st.session_state.match_counter = 0
        
        col_p1, col_p2 = st.columns(2)
        p_options = ["Antonio", "Andrea", "Fabio", "Esterno"]
        with col_p1: g1 = st.selectbox("Giocatore 1", p_options, index=p_options.index(user_sel) if user_sel in p_options else 0)
        with col_p2: g2 = st.selectbox("Giocatore 2", p_options, index=1 if user_sel != "Andrea" else 0)

        # Inizializzazione DataFrame
        df_key = f"df_init_match_{st.session_state.match_counter}"
        if df_key not in st.session_state:
            st.session_state[df_key] = pd.DataFrame(
                [{"Bey G1": "-", "Bey G2": "-", "Punti": "-"} for _ in range(13)],
                index=range(1, 14)
            )

        def get_meta_beys():
            beys = []
            if os.path.exists("meta.csv"):
                import csv
                for encoding in ['utf-8', 'latin-1']:
                    try:
                        with open("meta.csv", "r", encoding=encoding) as f:
                            reader = csv.reader(f)
                            next(reader, None) # Salta l'intestazione
                            for parts in reader:
                                if len(parts) >= 6:
                                    comps = [p.strip() for p in parts[:6] if p.strip()]
                                    if comps: beys.append(" ".join(comps))
                        break
                    except Exception:
                        pass
            return sorted(list(set(beys)))

        def get_bey_names(player_name, suffix):
            names = ["-"]
            if player_name == "Esterno":
                with st.expander(f"⚙️ Configura Bey Esterni ({suffix})"):
                    meta_list = ["Inserisci manualmente"] + get_meta_beys()
                    for i in range(3):
                        sel = st.selectbox(f"Seleziona Bey {i+1} ({suffix})", meta_list, key=f"ext_sel_{suffix}_{i}")
                        if sel == "Inserisci manualmente":
                            manual_val = st.text_input(f"Nome manuale Bey {i+1} ({suffix})", f"Esterno {i+1}", key=f"ext_{suffix}_{i}")
                            names.append(manual_val)
                        else:
                            names.append(sel)
            else:
                p_beys = st.session_state.users[player_name]["decks"]["beys"]
                for bey in p_beys:
                    n, _, _ = get_bey_name_and_comps(bey)
                    if n and n != "Nuovo Beyblade":
                        names.append(n)
            
            # --- LOGICA DI PROTEZIONE ---
            current_table_values = st.session_state[df_key][f"Bey {suffix}"].unique().tolist()
            for val in current_table_values:
                if val not in names:
                    names.append(val)
            
            return sorted(list(set(names)))

        # Generiamo le liste opzioni "protette"
        beys_g1 = get_bey_names(g1, "G1")
        beys_g2 = get_bey_names(g2, "G2")
        punteggi = ["-", "1-0", "2-0", "3-0", "0-1", "0-2", "0-3"]

        edited_df = st.data_editor(
            st.session_state[df_key],
            column_config={
                "Bey G1": st.column_config.SelectboxColumn("Bey G1", options=beys_g1, width="medium"),
                "Bey G2": st.column_config.SelectboxColumn("Bey G2", options=beys_g2, width="medium"),
                "Punti": st.column_config.SelectboxColumn("Punti", options=punteggi, width="small"),
            },
            use_container_width=True,
            hide_index=True,
            key=f"editor_active_{st.session_state.match_counter}" 
        )
        
        # AGGIORNAMENTO STATO
        if not edited_df.equals(st.session_state[df_key]):
            st.session_state[df_key] = edited_df
            st.rerun()

        # --- CALCOLO PUNTEGGIO TOTALE ---
        tot_g1 = 0
        tot_g2 = 0
        valid_rows = edited_df[edited_df["Punti"] != "-"]
        for _, row in valid_rows.iterrows():
            p1_val, p2_val = map(int, row["Punti"].split("-"))
            tot_g1 += p1_val
            tot_g2 += p2_val

        # --- VISUALIZZAZIONE TABELLA PUNTEGGIO (HTML/CSS per layout centrato) ---
        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; 
                        background-color: #1e293b; border: 1px solid #334155; 
                        border-radius: 8px; padding: 15px 20px; margin: 15px 0px;">
                <div style="flex: 1; text-align: left; font-size: 20px; font-weight: bold; color: #f1f5f9;">
                    {g1}
                </div>
                <div style="flex: 1; text-align: center; font-size: 28px; font-weight: 900; color: #3b82f6;">
                    {tot_g1} - {tot_g2}
                </div>
                <div style="flex: 1; text-align: right; font-size: 20px; font-weight: bold; color: #f1f5f9;">
                    {g2}
                </div>
            </div>
        """, unsafe_allow_html=True)


        # --- BOTTONE SALVATAGGIO ---
        if st.button("🚀 SALVA MATCH NEL CLOUD", use_container_width=True, type="primary"):
            if valid_rows.empty:
                st.warning("Compila almeno un round.")
            else:
                now_str = datetime.now().strftime("%d/%m/%Y")
                new_records = []
                for _, row in valid_rows.iterrows():
                    p1_raw, p2_raw = map(int, row["Punti"].split("-"))
                    # Calcolo i valori per i singoli record salvati
                    val_g1, val_g2 = (p1_raw, -p1_raw) if p1_raw > p2_raw else (-p2_raw, p2_raw)
                    new_records.append({
                        "Data": now_str, "NomeGiocatore1": g1, "BeyG1": row["Bey G1"],
                        "NomeGiocatore2": g2, "BeyG2": row["Bey G2"],
                        "PunteggioBeyG1": val_g1, "PunteggioBeyG2": val_g2
                    })
                
                with st.spinner("Aggiornamento archivio..."):
                    full_archive = github_action("stats", method="GET") or []
                    full_archive.extend(new_records)
                    if github_action("stats", full_archive, "PUT"):
                        st.success("Scontri archiviati con successo!")
                        st.session_state.match_counter += 1
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Errore salvataggio statistiche.")

        st.markdown("---")
        st.markdown("### 📥 Esporta Statistiche in Excel")
        
        start_date = st.date_input("Esporta dati a partire da:", value=datetime.today().date())
        
        if st.button("⚙️ Prepara File Excel", use_container_width=True):
            with st.spinner("Recupero dati e generazione Excel..."):
                stats_data = github_action("stats", method="GET") or []
                if not stats_data:
                    st.warning("Nessun dato presente nel registro.")
                else:
                    filtered_data = []
                    for row in stats_data:
                        d_str = row.get("Data", "")
                        try:
                            row_date = datetime.strptime(d_str, "%d/%m/%Y").date()
                        except ValueError:
                            try:
                                row_date = datetime.strptime(d_str, "%Y-%m-%d %H:%M:%S").date()
                            except ValueError:
                                row_date = datetime.min.date()
                                
                        if row_date >= start_date:
                            filtered_data.append(row)
                            
                    if not filtered_data:
                        st.warning("Nessun dato trovato a partire da questa data.")
                    else:
                        df_history = pd.DataFrame(filtered_data)
                        
                        df1 = df_history[['BeyG1', 'PunteggioBeyG1']].rename(columns={'BeyG1': 'Bey', 'PunteggioBeyG1': 'Score'})
                        df2 = df_history[['BeyG2', 'PunteggioBeyG2']].rename(columns={'BeyG2': 'Bey', 'PunteggioBeyG2': 'Score'})
                        
                        df_concat = pd.concat([df1, df2])
                        df_concat['Score'] = pd.to_numeric(df_concat['Score'], errors='coerce').fillna(0)
                        df_scores = df_concat.groupby('Bey')['Score'].sum().reset_index().sort_values(by='Score', ascending=False)
                        
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df_history.to_excel(writer, sheet_name='match history', index=False)
                            worksheet_history = writer.sheets['match history']
                            worksheet_history.autofilter(0, 0, len(df_history), len(df_history.columns) - 1)
                            
                            df_scores.to_excel(writer, sheet_name='Punteggi Beyblade', index=False)
                            
                            for u in ["Antonio", "Andrea", "Fabio"]:
                                if 'NomeGiocatore1' in df_history.columns and 'NomeGiocatore2' in df_history.columns:
                                    df_u = df_history[(df_history['NomeGiocatore1'] == u) | (df_history['NomeGiocatore2'] == u)]
                                else:
                                    df_u = pd.DataFrame() 
                                    
                                df_u.to_excel(writer, sheet_name=u, index=False)
                                worksheet_u = writer.sheets[u]
                                if not df_u.empty:
                                    worksheet_u.autofilter(0, 0, len(df_u), len(df_u.columns) - 1)
                                    
                        st.session_state.excel_bytes = output.getvalue()
                        st.success("✅ File Excel pronto!")

        if 'excel_bytes' in st.session_state:
            st.download_button(
                label="📥 SCARICA EXCEL (.xlsx)",
                data=st.session_state.excel_bytes,
                file_name=f"Beyblade_Match_History_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )

    # --- TAB 6: CLASSIFICA BEYBLADE ---

    with tab6:
        st.markdown("### 🏆 Classifica Globale Beyblade")
        
        stats_data = github_action("stats", method="GET") or []
        
        if not stats_data:
            st.info("Nessun match registrato finora nel cloud.")
        else:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                oggi = datetime.today().date()
                inizio_default = oggi - timedelta(days=30)
                date_range = st.date_input("📅 Range temporale", value=(inizio_default, oggi))
            
            with col_f2:
                opzioni_filtro = ["Tutti", "Antonio", "Andrea", "Fabio"]
                idx_default = opzioni_filtro.index(user_sel) if user_sel in opzioni_filtro else 0
                filtro_utente = st.selectbox("👤 Filtra per Utente", opzioni_filtro, index=idx_default)

            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_d, end_d = date_range
            elif isinstance(date_range, tuple) and len(date_range) == 1:
                start_d = end_d = date_range[0]
            else:
                start_d = end_d = date_range

            filtered_data = []
            for row in stats_data:
                d_str = row.get("Data", "")
                try:
                    row_date = datetime.strptime(d_str, "%d/%m/%Y").date()
                except ValueError:
                    try:
                        row_date = datetime.strptime(d_str, "%Y-%m-%d %H:%M:%S").date()
                    except ValueError:
                        row_date = datetime.min.date()
                
                if start_d <= row_date <= end_d:
                    filtered_data.append(row)

            if not filtered_data:
                st.warning("Nessun dato trovato per il periodo selezionato.")
            else:
                df_storico = pd.DataFrame(filtered_data)
                
                df_g1 = df_storico[['NomeGiocatore1', 'BeyG1', 'PunteggioBeyG1']].rename(columns={'NomeGiocatore1': 'Giocatore', 'BeyG1': 'Bey', 'PunteggioBeyG1': 'Punteggio'})
                df_g2 = df_storico[['NomeGiocatore2', 'BeyG2', 'PunteggioBeyG2']].rename(columns={'NomeGiocatore2': 'Giocatore', 'BeyG2': 'Bey', 'PunteggioBeyG2': 'Punteggio'})
                
                df_totale = pd.concat([df_g1, df_g2])
                
                if filtro_utente != "Tutti":
                    df_totale = df_totale[df_totale['Giocatore'] == filtro_utente]
                
                df_totale['Punteggio'] = pd.to_numeric(df_totale['Punteggio'], errors='coerce').fillna(0)
                
                # --- NUOVA LOGICA DI CALCOLO CLASSIFICA ---
                # Raggruppiamo contando le partite e sommando i punti
                df_classifica = df_totale.groupby('Bey').agg(
                    Partite=('Punteggio', 'count'),
                    Bilancio_Punti=('Punteggio', 'sum')
                ).reset_index()
                
                # Calcoliamo la media arrotondata al primo decimale
                df_classifica['Media_Punti'] = (df_classifica['Bilancio_Punti'] / df_classifica['Partite']).round(1)
                
                # Rinominiamo le colonne per chiarezza visiva
                df_classifica = df_classifica.rename(columns={
                    'Bilancio_Punti': 'Punti Totali',
                    'Media_Punti': 'Media Punti'
                })
                
                # Ordiniamo per Punti Totali (decrescente) e sistemiamo l'indice
                df_classifica = df_classifica.sort_values(by='Punti Totali', ascending=False)
                df_classifica.index = range(1, len(df_classifica) + 1)
                
                # Mostriamo la tabella forzando la formattazione a 1 decimale per la colonna media
                st.dataframe(
                    df_classifica, 
                    use_container_width=True,
                    column_config={
                        "Media Punti": st.column_config.NumberColumn("Media Punti", format="%.1f")
                    }
                )

elif menu_scelta == "Meta":
    tab_rank, tab_blades = st.tabs(["🏆 Ranking", "🗡️ Blades"])

    # --- FUNZIONE DI CARICAMENTO DATI ---
    @st.cache_data
    def load_meta_data():
        if os.path.exists("meta.csv"):
            try:
                return pd.read_csv("meta.csv", encoding="utf-8")
            except Exception:
                return pd.read_csv("meta.csv", encoding="latin-1")
        return pd.DataFrame()

    df_meta = load_meta_data()

    # --- TAB RANKING ---
    with tab_rank:
        st.markdown("### 🏆 Ranking Meta WBO")
        
        if not df_meta.empty:
            # Identifichiamo le colonne dei pezzi da unire
            colonne_componenti = [
                "Lock Chip", "Over Blade", "Main/Metal Blade (CX) / Blade (UX/BX)", 
                "Assist Blade", "Ratchet", "Bit"
            ]
            colonne_extra = ["Points", "Combo Rank", "Rank Change"]
            
            colonne_presenti_comp = [c for c in colonne_componenti if c in df_meta.columns]
            colonne_presenti_extra = [c for c in colonne_extra if c in df_meta.columns]
            
            df_rank = df_meta[colonne_presenti_comp + colonne_presenti_extra].copy()
            
            # 1. Unione delle colonne dei pezzi in un'unica stringa
            def unisci_combo(row):
                parti = [str(row[c]).strip() for c in colonne_presenti_comp if pd.notna(row[c]) and str(row[c]).strip() != ""]
                return " ".join(parti)
            
            df_rank.insert(0, "Combo", df_rank.apply(unisci_combo, axis=1))
            
            # --- LOGICA FILTRO PER POSSEDUTI ---
            filtra_posseduti = st.checkbox("✅ Filtra per posseduti", value=False, help="Mostra solo i Beyblade di cui hai tutte le componenti nell'inventario.")
            
            if filtra_posseduti:
                # Estraiamo tutti i pezzi posseduti dall'utente (chiavi dell'inventario con valore > 0)
                inv_utente = user_data.get("inv", {})
                pezzi_posseduti = set()
                lock_chips_posseduti = set()
                
                for cat, items in inv_utente.items():
                    for nome, qta in items.items():
                        if qta > 0:
                            pezzi_posseduti.add(nome)
                            if cat == "lock_chip":
                                lock_chips_posseduti.add(nome)
                
                lock_chips_metal = {"Emperor", "Valkyrie"}
                # Ha almeno un lock chip Metal?
                ha_metal = any(lc in lock_chips_metal for lc in lock_chips_posseduti)
                # Ha almeno un lock chip Plastic? (Qualsiasi lock chip che non è in lock_chips_metal)
                ha_plastic = any(lc not in lock_chips_metal for lc in lock_chips_posseduti)
                
                def possiede_tutte_componenti(row):
                    for col in colonne_presenti_comp:
                        pezzo_richiesto = str(row[col]).strip()
                        if not pezzo_richiesto or pezzo_richiesto == "nan":
                            continue # Componente non richiesta
                            
                        if col == "Lock Chip":
                            if pezzo_richiesto == "Metal" and not ha_metal:
                                return False
                            elif pezzo_richiesto == "Plastic" and not ha_plastic:
                                return False
                        else:
                            if pezzo_richiesto not in pezzi_posseduti:
                                return False
                    return True

                # Applichiamo il filtro riga per riga e manteniamo solo quelle valide
                mask_posseduti = df_rank.apply(possiede_tutte_componenti, axis=1)
                df_rank = df_rank[mask_posseduti]

            # Rimuoviamo le colonne singole dopo aver filtrato
            df_rank = df_rank.drop(columns=colonne_presenti_comp)
            
            if "Rank Change" in df_rank.columns:
                df_rank["Rank Change"] = df_rank["Rank Change"].astype(str)
                df_rank["Rank Change"] = df_rank["Rank Change"].replace(
                    {r'.*â¬†.*': '⬆️', r'.*â¬‡.*': '⬇️', r'.*â€”.*': '—'}, regex=True
                )
                df_rank["Rank Change"] = df_rank["Rank Change"].replace({'nan': '-'})
            
            if "Combo Rank" in df_rank.columns:
                df_rank["Combo Rank"] = pd.to_numeric(df_rank["Combo Rank"], errors='coerce')
                
            col_ordine = ["Combo", "Points", "Combo Rank", "Rank Change"]
            col_ordine_presenti = [c for c in col_ordine if c in df_rank.columns]
            df_rank = df_rank[col_ordine_presenti]
                
            ricerca_rank = st.text_input("🔍 Ricerca", key="search_rank").lower()
            
            if "Combo Rank" in df_rank.columns:
                df_rank = df_rank.sort_values(by="Combo Rank", ascending=True)
                
            if ricerca_rank:
                mask = df_rank.astype(str).apply(lambda x: x.str.lower().str.contains(ricerca_rank, regex=False)).any(axis=1)
                df_rank = df_rank[mask]
                
            st.dataframe(df_rank, use_container_width=True, hide_index=True)
            
        else:
            st.warning("⚠️ File 'meta.csv' non trovato. Assicurati che sia presente nella directory.")

    # --- TAB BLADES ---
    with tab_blades:
        st.markdown("### 🗡️ Classifica Punti Blades")
        
        if not df_meta.empty:
            col_nome_blade = "Main/Metal Blade (CX) / Blade (UX/BX) Name"
            col_punti_blade = "Main/Metal Blade (CX) / Blade (UX/BX) Points"
            
            if col_nome_blade in df_meta.columns and col_punti_blade in df_meta.columns:
                df_blades = df_meta[[col_nome_blade, col_punti_blade]].copy()
                df_blades = df_blades.dropna(subset=[col_nome_blade])
                df_blades[col_punti_blade] = pd.to_numeric(df_blades[col_punti_blade], errors='coerce')
                
                ricerca_blade = st.text_input("🔍 Ricerca", key="search_blade").lower()
                
                df_blades = df_blades.sort_values(by=col_punti_blade, ascending=False)
                
                if ricerca_blade:
                    df_blades = df_blades[df_blades[col_nome_blade].astype(str).str.lower().str.contains(ricerca_blade, regex=False)]
                    
                st.dataframe(df_blades, use_container_width=True, hide_index=True)
            else:
                st.error("⚠️ Colonne delle Blades non trovate nel file meta.csv. Verifica l'intestazione.")
        else:
            st.warning("⚠️ File 'meta.csv' non trovato. Assicurati che sia presente nella directory.")
