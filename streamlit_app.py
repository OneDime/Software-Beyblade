import streamlit as st
import pandas as pd
import hashlib
import os
import json
import requests
import base64
from PIL import Image

# =========================
# 1. CONFIGURAZIONE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

# =========================
# 2. LOGICA GITHUB
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
    st.success("✅ SALVATO SU CLOUD!")

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
# 3. GESTIONE UTENTE (URL & CACHE)
# =========================
if 'users' not in st.session_state:
    cloud = load_cloud()
    st.session_state.users = cloud if cloud else {u: {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {str(i): {} for i in range(3)}}]} for u in ["Antonio", "Andrea", "Fabio"]}

# Leggi utente da URL
user_list = ["Antonio", "Andrea", "Fabio"]
query_user = st.query_params.get("user", "Antonio")
if query_user not in user_list: query_user = "Antonio"

st.sidebar.title("👤 Account")
# Seleziona l'utente in base all'URL
user_sel = st.sidebar.radio("Seleziona Utente:", user_list, index=user_list.index(query_user))

# Se cambi nel menu, aggiorna URL e ricarica
if user_sel != query_user:
    st.query_params["user"] = user_sel
    st.rerun()

st.sidebar.write(f"📡 Login attuale: **{user_sel}**")

user_data = st.session_state.users[user_sel]

# =========================
# 4. DATI & IMMAGINI
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

df_db, global_img_map = load_db()

def get_img(url, size=(100, 100)):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join("images", f"{h}.png")
    if os.path.exists(path): return Image.open(path).resize(size, Image.Resampling.LANCZOS)
    return None

# =========================
# 5. UI PRINCIPALE
# =========================
st.markdown(f"<h1 style='text-align: center;'>Officina di {user_sel}</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab1:
    search_q = st.text_input("Cerca componente...", "").lower()
    filtered = df_db[df_db['_search'].str.contains(search_q)] if search_q else df_db.head(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.write(f"### {row['name']}")
            img = get_img(row['blade_image'] or row['beyblade_page_image'], size=(150, 150))
            if img: st.image(img)
            if st.button("Aggiungi tutto all'inventario", key=f"all_{i}"):
                comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"),
                         ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"),
                         ("ratchet_integrated_bit", "ratchet_integrated_bit")]
                for ck, ik in comps:
                    val = row[ck]
                    if val and val != "n/a": user_data["inv"][ik][val] = user_data["inv"][ik].get(val, 0) + 1
                save_all(); st.rerun()

with tab2:
    for cat, items in user_data["inv"].items():
        if items:
            with st.expander(cat.upper()):
                for n, q in list(items.items()):
                    c1, c2 = st.columns([0.8, 0.2])
                    c1.write(f"**{n}** ({q})")
                    if c2.button("🗑️", key=f"del_{cat}_{n}"):
                        user_data["inv"][cat][n] -= 1
                        if user_data["inv"][cat][n] <= 0: del user_data["inv"][cat][n]
                        save_all(); st.rerun()

with tab3:
    # --- TASTO SALVA GLOBALE (SEMPRE IN CIMA) ---
    st.markdown("---")
    if st.button("💾 SALVA TUTTI I DECK SU CLOUD", type="primary", use_container_width=True):
        save_all()
    st.markdown("---")

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
                vals = deck["slots"][s_key]
                
                st.markdown(f"**Slot {s_idx+1}**")
                sel_tipo = st.selectbox(f"Sistema Slot {s_idx+1}", tipologie, key=f"t_{d_idx}_{s_idx}")
                th = "Theory" in sel_tipo
                
                # Funzione di selezione semplice
                def draw_sel(label, cat, k):
                    opts = get_options(cat, th)
                    curr = vals.get(k, "-")
                    idx = opts.index(curr) if curr in opts else 0
                    sel = st.selectbox(label, opts, index=idx, key=f"s_{d_idx}_{s_idx}_{k}")
                    deck["slots"][s_key][k] = sel

                if "BX/UX" in sel_tipo and "+RIB" not in sel_tipo:
                    draw_sel("Blade", "blade", "b")
                    draw_sel("Ratchet", "ratchet", "r")
                    draw_sel("Bit", "bit", "bi")
                elif "CX" in sel_tipo and "+RIB" not in sel_tipo:
                    draw_sel("Lock Bit", "lock_bit", "lb")
                    draw_sel("Main Blade", "main_blade", "mb")
                    draw_sel("Assist Blade", "assist_blade", "ab")
                    draw_sel("Ratchet", "ratchet", "r")
                    draw_sel("Bit", "bit", "bi")
                elif "+RIB" in sel_tipo:
                    if "CX" in sel_tipo:
                        draw_sel("Lock Bit", "lock_bit", "lb"); draw_sel("Main Blade", "main_blade", "mb"); draw_sel("Assist Blade", "assist_blade", "ab")
                    else: draw_sel("Blade", "blade", "b")
                    draw_sel("RIB", "ratchet_integrated_bit", "rib")

            # --- TASTI DI CONTROLLO DEL SINGOLO DECK ---
            st.divider()
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button(f"✏️ Rinomina", key=f"ren_{d_idx}"):
                    st.info("Funzione rinomina attiva (scrivi sopra)") # Semplificato per test
            with c2:
                if st.button(f"💾 SALVA DECK", key=f"sv_{d_idx}"):
                    save_all()
            with c3:
                if st.button(f"🗑️ Elimina", key=f"dl_{d_idx}"):
                    user_data["decks"].pop(d_idx); save_all(); st.rerun()

    if st.button("➕ Crea Nuovo Deck"):
        user_data["decks"].append({"name": f"DECK {len(user_data['decks'])+1}", "slots": {str(i): {} for i in range(3)}})
        save_all(); st.rerun()