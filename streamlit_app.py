import streamlit as st
import pandas as pd
import hashlib
import os
import json
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# =========================
# CONFIGURAZIONE & STILE (INTOCCABILE)
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    .user-title { font-size: 28px !important; font-weight: bold; margin-bottom: 20px; color: #f1f5f9; }
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
    div.stButton > button {
        width: auto !important; min-width: 150px !important;
        height: 30px !important; background-color: #334155 !important; color: white !important;
        border: 1px solid #475569 !important; border-radius: 4px !important;
    }
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; text-align: left !important; margin-bottom: 5px !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# FUNZIONI SALVATAGGIO (GSHEETS)
# =========================
def save_cloud():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        inv_list = []
        deck_list = []
        for u, data in st.session_state.users.items():
            inv_list.append({"Utente": u, "Dati": json.dumps(data["inv"])})
            deck_list.append({"Utente": u, "Dati": json.dumps(data["decks"])})
        
        conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], worksheet="inventario", data=pd.DataFrame(inv_list))
        conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], worksheet="decks", data=pd.DataFrame(deck_list))
    except Exception as e:
        st.sidebar.warning("Salvataggio Cloud non riuscito (verifica permessi foglio)")

def load_cloud():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_inv = conn.read(worksheet="inventario", ttl=0)
        df_deck = conn.read(worksheet="decks", ttl=0)
        new_users = {}
        for u in ["Antonio", "Andrea", "Fabio"]:
            u_inv = df_inv[df_inv["Utente"] == u]["Dati"].values
            u_deck = df_deck[df_deck["Utente"] == u]["Dati"].values
            new_users[u] = {
                "inv": json.loads(u_inv[0]) if len(u_inv) > 0 else {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]},
                "decks": json.loads(u_deck[0]) if len(u_deck) > 0 else [{"name": "DECK 1", "slots": {str(i): {} for i in range(3)}}]
            }
        return new_users
    except:
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
    if os.path.exists(path):
        return Image.open(path).resize(size, Image.Resampling.LANCZOS)
    return None

# =========================
# INIZIALIZZAZIONE
# =========================
if 'users' not in st.session_state:
    cloud = load_cloud()
    st.session_state.users = cloud if cloud else {
        "Antonio": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {str(i): {} for i in range(3)}}]},
        "Andrea": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {str(i): {} for i in range(3)}}]},
        "Fabio": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {str(i): {} for i in range(3)}}]}
    }

st.sidebar.title("👤 Account")
user_sel = st.sidebar.radio("Seleziona Utente:", ["Antonio", "Andrea", "Fabio"])
user_data = st.session_state.users[user_sel]

if 'exp_state' not in st.session_state: st.session_state.exp_state = {}
if 'edit_name_idx' not in st.session_state: st.session_state.edit_name_idx = None

df, global_img_map = load_db()

# =========================
# UI PRINCIPALE
# =========================
st.markdown(f"<div class='user-title'>Officina di {user_sel}</div>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab1:
    search_q = st.text_input("Cerca...", "").lower()
    filtered = df[df['_search'].str.contains(search_q)] if search_q else df.head(3)
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
                st.toast("Aggiunto!")
            st.markdown("<hr>", unsafe_allow_html=True)
            for ck, ik in comps:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name-centered'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        user_data["inv"][ik][val] = user_data["inv"][ik].get(val, 0) + 1
                        save_cloud()
                        st.toast(f"Aggiunto: {val}")

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
                        save_cloud()
                        st.rerun()

with tab3:
    def get_options(cat, theory=False):
        if theory:
            csv_map = {"lock_bit": "lock_chip", "blade": "blade", "main_blade": "main_blade", "assist_blade": "assist_blade", "ratchet": "ratchet", "bit": "bit", "ratchet_integrated_bit": "ratchet_integrated_bit"}
            return ["-"] + sorted([x for x in df[csv_map.get(cat, cat)].unique().tolist() if x and x != "n/a"])
        return ["-"] + sorted(list(user_data["inv"][cat].keys()))

    tipologie = ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", "BX/UX Theory", "CX Theory", "BX/UX+RIB Theory", "CX+RIB Theory"]

    for d_idx, deck in enumerate(user_data["decks"]):
        with st.expander(f"{deck['name'].upper()}", expanded=True):
            for s_idx in range(3):
                s_key = str(s_idx)
                sels = deck["slots"][s_key] if s_key in deck["slots"] else {}
                titolo = " ".join([v for v in sels.values() if v and v != "-"]) or f"SLOT {s_idx+1}"
                exp_key = f"{user_sel}-{d_idx}-{s_idx}"
                
                with st.expander(titolo.upper(), expanded=st.session_state.exp_state.get(exp_key, False)):
                    tipo = st.selectbox("Sistema", tipologie, key=f"ty_{exp_key}")
                    is_th = "Theory" in tipo
                    curr = {}
                    if "BX/UX" in tipo and "+RIB" not in tipo:
                        curr['b'] = st.selectbox("Blade", get_options("blade", is_th), key=f"b_{exp_key}")
                        curr['r'] = st.selectbox("Ratchet", get_options("ratchet", is_th), key=f"r_{exp_key}")
                        curr['bi'] = st.selectbox("Bit", get_options("bit", is_th), key=f"bi_{exp_key}")
                    elif "CX" in tipo and "+RIB" not in tipo:
                        curr['lb'] = st.selectbox("Lock Bit", get_options("lock_bit", is_th), key=f"lb_{exp_key}")
                        curr['mb'] = st.selectbox("Main Blade", get_options("main_blade", is_th), key=f"mb_{exp_key}")
                        curr['ab'] = st.selectbox("Assist Blade", get_options("assist_blade", is_th), key=f"ab_{exp_key}")
                        curr['r'] = st.selectbox("Ratchet", get_options("ratchet", is_th), key=f"r_{exp_key}")
                        curr['bi'] = st.selectbox("Bit", get_options("bit", is_th), key=f"bi_{exp_key}")
                    elif "+RIB" in tipo:
                        if "CX" in tipo:
                            curr['lb'] = st.selectbox("Lock Bit", get_options("lock_bit", is_th), key=f"lb_{exp_key}")
                            curr['mb'] = st.selectbox("Main Blade", get_options("main_blade", is_th), key=f"mb_{exp_key}")
                            curr['ab'] = st.selectbox("Assist Blade", get_options("assist_blade", is_th), key=f"ab_{exp_key}")
                        else:
                            curr['b'] = st.selectbox("Blade", get_options("blade", is_th), key=f"b_{exp_key}")
                        curr['rib'] = st.selectbox("RIB", get_options("ratchet_integrated_bit", is_th), key=f"rib_{exp_key}")

                    cols = st.columns(5)
                    for idx, (k, v) in enumerate(curr.items()):
                        if v != "-":
                            img_obj = get_img(global_img_map.get(v))
                            if img_obj: cols[idx].image(img_obj)

                    if deck["slots"].get(s_key) != curr:
                        deck["slots"][s_key] = curr
                        save_cloud()
                        st.session_state.exp_state[exp_key] = True
                        st.rerun()

            c1, c2, _ = st.columns([0.2, 0.2, 0.6])
            if c1.button("📝 Rinomina", key=f"ren_{user_sel}_{d_idx}"):
                st.session_state.edit_name_idx = f"{user_sel}_{d_idx}"
                st.rerun()
            if c2.button("🗑️ Elimina", key=f"del_{user_sel}_{d_idx}", type="primary"):
                user_data["decks"].pop(d_idx)
                save_cloud()
                st.rerun()
            if st.session_state.edit_name_idx == f"{user_sel}_{d_idx}":
                n_name = st.text_input("Nuovo nome:", deck['name'])
                if st.button("Conferma"):
                    deck['name'] = n_name
                    st.session_state.edit_name_idx = None
                    save_cloud()
                    st.rerun()

    if st.button("➕ Nuovo Deck"):
        user_data["decks"].append({"name": f"DECK {len(user_data['decks'])+1}", "slots": {str(i): {} for i in range(3)}})
        save_cloud()
        st.rerun()