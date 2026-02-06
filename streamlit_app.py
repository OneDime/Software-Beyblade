import streamlit as st
import pandas as pd
import hashlib
import os
import json
import requests
import base64
from PIL import Image

# =========================
# 1. SETUP & PERSISTENZA UTENTE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

# Lista utenti fissa
UTENTI = ["Antonio", "Andrea", "Fabio"]

# Recupero utente dall'URL
query_params = st.query_params
utente_url = query_params.get("user", "Antonio")

# Se l'utente nell'URL non è valido, forziamo Antonio
if utente_url not in UTENTI:
    utente_url = "Antonio"

# Sidebar per il cambio utente
st.sidebar.title("👤 Account")
user_sel = st.sidebar.radio("Sei loggato come:", UTENTI, index=UTENTI.index(utente_url))

# SE L'UTENTE CAMBIA NEL MENU: aggiorniamo l'URL e ricarichiamo subito
if user_sel != utente_url:
    st.query_params["user"] = user_sel
    st.rerun()

# =========================
# 2. FUNZIONI GITHUB
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
    st.toast("✅ Dati salvati su GitHub!", icon="💾")

def load_cloud():
    inv_cloud = github_action("inv", method="GET")
    deck_cloud = github_action("decks", method="GET")
    if inv_cloud and deck_cloud:
        new_users = {}
        for u in UTENTI:
            new_users[u] = {
                "inv": inv_cloud.get(u, {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}),
                "decks": deck_cloud.get(u, [{"name": "DECK 1", "slots": {str(i): {} for i in range(3)}}])
            }
        return new_users
    return None

# =========================
# 3. CARICAMENTO DATI
# =========================
if 'users' not in st.session_state:
    cloud = load_cloud()
    if cloud:
        st.session_state.users = cloud
    else:
        st.session_state.users = {u: {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {str(i): {} for i in range(3)}}]} for u in UTENTI}

user_data = st.session_state.users[user_sel]

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

df_db, global_img_map = load_db()

def get_img(url, size=(100, 100)):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join("images", f"{h}.png")
    if os.path.exists(path): return Image.open(path).resize(size, Image.Resampling.LANCZOS)
    return None

# =========================
# 4. INTERFACCIA PRINCIPALE
# =========================
st.title(f"🛠️ Officina di {user_sel}")

tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab1:
    search_q = st.text_input("Cerca pezzo...", "").lower()
    filtered = df_db[df_db['_search'].str.contains(search_q)] if search_q else df_db.head(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.subheader(row['name'])
            img = get_img(row['blade_image'] or row['beyblade_page_image'], size=(120, 120))
            if img: st.image(img)
            if st.button("Aggiungi all'inventario", key=f"add_{i}"):
                comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"),
                         ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"),
                         ("ratchet_integrated_bit", "ratchet_integrated_bit")]
                for ck, ik in comps:
                    val = row[ck]
                    if val and val != "n/a": user_data["inv"][ik][val] = user_data["inv"][ik].get(val, 0) + 1
                save_all(); st.rerun()

with tab2:
    st.info("Le modifiche qui si salvano subito.")
    for cat, items in user_data["inv"].items():
        if items:
            with st.expander(f"📂 {cat.upper()}"):
                for n, q in list(items.items()):
                    c1, c2 = st.columns([0.8, 0.2])
                    c1.write(f"**{n}** (x{q})")
                    if c2.button("🗑️", key=f"del_{cat}_{n}"):
                        user_data["inv"][cat][n] -= 1
                        if user_data["inv"][cat][n] <= 0: del user_data["inv"][cat][n]
                        save_all(); st.rerun()

with tab3:
    # --- POSIZIONE DI SICUREZZA: IL TASTO SALVA GENERALE ---
    st.warning("⚠️ Ricorda di salvare dopo ogni modifica ai deck!")
    if st.button("💾 SALVA TUTTI I DECK (GLOBAL)", type="primary", use_container_width=True):
        save_all()
        st.rerun()
    
    st.markdown("---")

    def get_options(cat, theory=False):
        if theory:
            csv_m = {"lock_bit": "lock_chip", "blade": "blade", "main_blade": "main_blade", "assist_blade": "assist_blade", "ratchet": "ratchet", "bit": "bit", "ratchet_integrated_bit": "ratchet_integrated_bit"}
            return ["-"] + sorted([x for x in df_db[csv_m.get(cat, cat)].unique().tolist() if x and x != "n/a"])
        return ["-"] + sorted(list(user_data["inv"].get(cat, {}).keys()))

    # Se l'utente non ha deck, ne creiamo uno
    if not user_data["decks"]:
        user_data["decks"] = [{"name": "DECK 1", "slots": {str(i): {} for i in range(3)}}]

    for d_idx, deck in enumerate(user_data["decks"]):
        with st.container(border=True):
            col_titolo, col_del = st.columns([0.8, 0.2])
            col_titolo.subheader(f"📁 {deck['name']}")
            if col_del.button("🗑️", key=f"rm_dk_{d_idx}"):
                user_data["decks"].pop(d_idx)
                save_all(); st.rerun()

            for s_idx in range(3):
                s_key = str(s_idx)
                if s_key not in deck["slots"]: deck["slots"][s_key] = {}
                vals = deck["slots"][s_key]
                
                with st.expander(f"Slot {s_idx+1}: {list(vals.values())[0] if vals else 'Vuoto'}"):
                    tipo = st.selectbox("Sistema", ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", "Theory"], key=f"t_{d_idx}_{s_idx}")
                    th = "Theory" in tipo
                    
                    def build_sel(label, cat, k):
                        opts = get_options(cat, th)
                        curr = vals.get(k, "-")
                        idx = opts.index(curr) if curr in opts else 0
                        sel = st.selectbox(label, opts, index=idx, key=f"s_{d_idx}_{s_idx}_{k}")
                        deck["slots"][s_key][k] = sel

                    if "BX/UX" in tipo and "+RIB" not in tipo:
                        build_sel("Blade", "blade", "b"); build_sel("Ratchet", "ratchet", "r"); build_sel("Bit", "bit", "bi")
                    elif "CX" in tipo and "+RIB" not in tipo:
                        build_sel("Lock Bit", "lock_bit", "lb"); build_sel("Main Blade", "main_blade", "mb"); build_sel("Assist Blade", "assist_blade", "ab")
                        build_sel("Ratchet", "ratchet", "r"); build_sel("Bit", "bit", "bi")
                    elif "+RIB" in tipo:
                        if "CX" in tipo:
                            build_sel("Lock Bit", "lock_bit", "lb"); build_sel("Main Blade", "main_blade", "mb"); build_sel("Assist Blade", "assist_blade", "ab")
                        else: build_sel("Blade", "blade", "b")
                        build_sel("RIB", "ratchet_integrated_bit", "rib")
                    elif "Theory" in tipo:
                        build_sel("Blade/Main", "blade", "b"); build_sel("Ratchet", "ratchet", "r"); build_sel("Bit", "bit", "bi")

            # TASTO SALVA SINGOLO DECK (Sotto ogni deck)
            if st.button(f"💾 SALVA {deck['name']}", key=f"sv_single_{d_idx}"):
                save_all()
                st.rerun()

    st.markdown("---")
    if st.button("➕ AGGIUNGI NUOVO DECK"):
        user_data["decks"].append({"name": f"DECK {len(user_data['decks'])+1}", "slots": {str(i): {} for i in range(3)}})
        save_all()
        st.rerun()