import streamlit as st
import pandas as pd
import hashlib
import os
import json
import requests
import base64
from PIL import Image

# =========================
# 1. CONFIGURAZIONE (DEVE ESSERE LA PRIMA ISTRUZIONE)
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

# =========================
# 2. GESTIONE UTENTE & URL (PRIORITÀ ASSOLUTA)
# =========================
# Lista utenti
users_list = ["Antonio", "Andrea", "Fabio"]

# Leggiamo l'URL attuale
qp = st.query_params
url_user = qp.get("user", "Antonio") # Se non c'è nulla, default Antonio

# Validazione: se l'URL ha un nome strano, torniamo ad Antonio
if url_user not in users_list:
    url_user = "Antonio"

# CSS
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    .user-title { font-size: 28px !important; font-weight: bold; margin-bottom: 20px; color: #f1f5f9; text-align: center; width: 100%; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 15px !important;
        padding: 15px !important;
    }
    .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; text-align: center; }
    div.stButton > button { width: 100% !important; background-color: #334155 !important; color: white !important; border: 1px solid #475569 !important; }
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; }
    /* Evidenzia il tasto Salva */
    button[kind="primary"] { background-color: #2563eb !important; border-color: #3b82f6 !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# 3. SIDEBAR E CAMBIO UTENTE
# =========================
st.sidebar.title("👤 Account")

# Il widget parte selezionando quello che c'è nell'URL
try:
    idx = users_list.index(url_user)
except:
    idx = 0

user_sel = st.sidebar.radio("Seleziona Utente:", users_list, index=idx)

# SE L'UTENTE CAMBIA LA SELEZIONE:
if user_sel != url_user:
    # 1. Aggiorna l'URL
    st.query_params["user"] = user_sel
    # 2. Ricarica la pagina per applicare la modifica all'URL bar del browser
    st.rerun()

# =========================
# 4. LOGICA GITHUB & DATI
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

def save_all():
    inv_data = {u: d["inv"] for u, d in st.session_state.users.items()}
    deck_data = {u: d["decks"] for u, d in st.session_state.users.items()}
    github_action("inv", inv_data, "PUT")
    github_action("decks", deck_data, "PUT")
    st.toast("✅ SALVATAGGIO RIUSCITO!", icon="💾")

def load_cloud():
    inv_cloud = github_action("inv", method="GET")
    deck_cloud = github_action("decks", method="GET")
    if inv_cloud and deck_cloud:
        new_users = {}
        for u in users_list:
            new_users[u] = {
                "inv": inv_cloud.get(u, {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}),
                "decks": deck_cloud.get(u, [{"name": "DECK 1", "slots": {str(i): {} for i in range(3)}}])
            }
        return new_users
    return None

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
# 5. CARICAMENTO STATO
# =========================
if 'users' not in st.session_state:
    cloud = load_cloud()
    if cloud: st.session_state.users = cloud
    else:
        st.session_state.users = {u: {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {str(i): {} for i in range(3)}}]} for u in users_list}

user_data = st.session_state.users[user_sel]
df_db, global_img_map = load_db()

# =========================
# 6. INTERFACCIA
# =========================
st.markdown(f"<div class='user-title'>Officina di {user_sel}</div>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

# --- TAB 1: AGGIUNGI (INVARIATO) ---
with tab1:
    search_q = st.text_input("Cerca componente...", "").lower()
    filtered = df_db[df_db['_search'].str.contains(search_q)] if search_q else df_db.head(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.markdown(f"<div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
            img = get_img(row['blade_image'] or row['beyblade_page_image'], size=(150, 150))
            if img: st.image(img)
            if st.button("Aggiungi tutto all'inventario", key=f"all_{i}"):
                comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"),
                         ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"),
                         ("ratchet_integrated_bit", "ratchet_integrated_bit")]
                for ck, ik in comps:
                    val = row[ck]
                    if val and val != "n/a": user_data["inv"][ik][val] = user_data["inv"][ik].get(val, 0) + 1
                save_all() # Salva subito l'inventario (qui funziona bene)
                st.rerun()

# --- TAB 2: INVENTARIO (INVARIATO) ---
with tab2:
    st.info("Le modifiche qui sono salvate automaticamente.")
    for cat, items in user_data["inv"].items():
        if items:
            with st.expander(cat.replace('_', ' ').upper()):
                for n, q in list(items.items()):
                    c1, c2 = st.columns([0.8, 0.2])
                    c1.write(f"**{n}** (Quantità: {q})")
                    if c2.button("🗑️", key=f"del_inv_{user_sel}_{cat}_{n}"):
                        user_data["inv"][cat][n] -= 1
                        if user_data["inv"][cat][n] <= 0: del user_data["inv"][cat][n]
                        save_all()
                        st.rerun()

# --- TAB 3: DECK BUILDER (MODIFICATO CON TASTI VISIBILI) ---
with tab3:
    st.info("⚠️ ATTENZIONE: Modifica i componenti e poi clicca il tasto BLU 'SALVA DECK' per confermare.")

    def get_options(cat, theory=False):
        if theory:
            csv_m = {"lock_bit": "lock_chip", "blade": "blade", "main_blade": "main_blade", "assist_blade": "assist_blade", "ratchet": "ratchet", "bit": "bit", "ratchet_integrated_bit": "ratchet_integrated_bit"}
            return ["-"] + sorted([x for x in df_db[csv_m.get(cat, cat)].unique().tolist() if x and x != "n/a"])
        return ["-"] + sorted(list(user_data["inv"][cat].keys()))

    tipologie = ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", "BX/UX Theory", "CX Theory", "BX/UX+RIB Theory", "CX+RIB Theory"]
    
    for d_idx, deck in enumerate(user_data["decks"]):
        with st.expander(f"📁 {deck['name'].upper()}", expanded=True):
            
            # --- SLOT ---
            for s_idx in range(3):
                s_key = str(s_idx)
                if s_key not in deck["slots"]: deck["slots"][s_key] = {}
                vals = deck["slots"][s_key]
                
                parts = [v for v in vals.values() if v and v != "-"]
                t_label = " ".join(parts) if parts else f"Slot {s_idx+1}"
                
                with st.expander(t_label.upper()):
                    sys_key = f"sys_sel_{d_idx}_{s_idx}"
                    if sys_key not in st.session_state: st.session_state[sys_key] = "BX/UX"
                    
                    sel_tipo = st.selectbox("Sistema", tipologie, key=sys_key)
                    is_th = "Theory" in sel_tipo
                    
                    def smart_select(label, cat, k_part):
                        options = get_options(cat, is_th)
                        current = vals.get(k_part, "-")
                        try: idx = options.index(current)
                        except: idx = 0
                        # Qui aggiorniamo SOLO la variabile locale 'deck'. 
                        # Il salvataggio su Cloud avviene solo col tasto blu.
                        sel = st.selectbox(label, options, index=idx, key=f"sel_{d_idx}_{s_idx}_{k_part}")
                        deck["slots"][s_key][k_part] = sel
                        return sel

                    if "BX/UX" in sel_tipo and "+RIB" not in sel_tipo:
                        smart_select("Blade", "blade", "b")
                        smart_select("Ratchet", "ratchet", "r")
                        smart_select("Bit", "bit", "bi")
                    elif "CX" in sel_tipo and "+RIB" not in sel_tipo:
                        smart_select("Lock Bit", "lock_bit", "lb")
                        smart_select("Main Blade", "main_blade", "mb")
                        smart_select("Assist Blade", "assist_blade", "ab")
                        smart_select("Ratchet", "ratchet", "r")
                        smart_select("Bit", "bit", "bi")
                    elif "+RIB" in sel_tipo:
                        if "CX" in sel_tipo:
                            smart_select("Lock Bit", "lock_bit", "lb")
                            smart_select("Main Blade", "main_blade", "mb")
                            smart_select("Assist Blade", "assist_blade", "ab")
                        else: smart_select("Blade", "blade", "b")
                        smart_select("RIB", "ratchet_integrated_bit", "rib")
                    
                    cols = st.columns(5)
                    col_i = 0
                    for k, v in vals.items():
                        if v != "-":
                            img = get_img(global_img_map.get(v))
                            if img: cols[col_i % 5].image(img); col_i += 1

            st.divider()
            
            # --- BARRA DEI TASTI (SEMPRE VISIBILE) ---
            # Gestione Rinomina (Stato locale per mostrare input)
            ren_key = f"renaming_{d_idx}"
            if ren_key not in st.session_state: st.session_state[ren_key] = False

            if st.session_state[ren_key]:
                st.write("✏️ **Rinomina Deck:**")
                new_name = st.text_input("Nome:", value=deck['name'], key=f"input_ren_{d_idx}", label_visibility="collapsed")
                c_conf, c_ann = st.columns(2)
                if c_conf.button("Conferma", key=f"ok_ren_{d_idx}"):
                    deck['name'] = new_name
                    st.session_state[ren_key] = False
                    save_all()
                    st.rerun()
                if c_ann.button("Annulla", key=f"ko_ren_{d_idx}"):
                    st.session_state[ren_key] = False
                    st.rerun()
            else:
                # 3 COLONNE: RINOMINA | SALVA | ELIMINA
                col_ren, col_save, col_del = st.columns([1, 1.5, 1])
                
                with col_ren:
                    if st.button("✏️ Rinomina", key=f"btn_ren_{d_idx}"):
                        st.session_state[ren_key] = True
                        st.rerun()
                
                with col_save:
                    # Tasto PRIMARIO (Blu) - Questo è quello che salva su GitHub
                    if st.button("💾 SALVA DECK", key=f"btn_save_{d_idx}", type="primary"):
                        save_all()
                        st.rerun()
                
                with col_del:
                    if st.button("🗑️ Elimina", key=f"btn_del_{d_idx}"):
                        user_data["decks"].pop(d_idx)
                        save_all()
                        st.rerun()

    if st.button("➕ Crea Nuovo Deck", use_container_width=True):
        user_data["decks"].append({"name": f"DECK {len(user_data['decks'])+1}", "slots": {str(i): {} for i in range(3)}})
        save_all()
        st.rerun()