import streamlit as st
import pandas as pd
import hashlib
import os
import json
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE (ORIGINALE E INTOCCABILE)
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    
    .user-title { font-size: 28px !important; font-weight: bold; margin-bottom: 20px; color: #f1f5f9; }

    /* TAB AGGIUNGI (STILE ORIGINALE) */
    [data-testid="stVerticalBlock"] { text-align: center; align-items: center; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 15px !important;
        padding: 10px !important;
    }
    .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; }
    .comp-name-centered { font-size: 1.1rem; color: #cbd5e1; display: block; width: 100%; }
    hr { margin-top: 8px !important; margin-bottom: 8px !important; opacity: 0.3; }

    div.stButton > button {
        width: auto !important; min-width: 150px !important;
        height: 30px !important; background-color: #334155 !important; color: white !important;
        border: 1px solid #475569 !important; border-radius: 4px !important;
    }

    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; text-align: left !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# INIZIALIZZAZIONE DATI
# =========================
if 'users' not in st.session_state:
    st.session_state.users = {
        "Antonio": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]},
        "Andrea": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]},
        "Fabio": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]}
    }

if 'exp_state' not in st.session_state: st.session_state.exp_state = {}
if 'edit_name_idx' not in st.session_state: st.session_state.edit_name_idx = None

@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame(), {}
    df = pd.read_csv("beyblade_x.csv").fillna("")
    img_map = {}
    mapping_rules = [('lock_chip', 'lock_chip_image'), ('blade', 'blade_image'), ('main_blade', 'main_blade_image'), 
                     ('assist_blade', 'assist_blade_image'), ('ratchet', 'ratchet_image'), ('bit', 'bit_image'),
                     ('ratchet_integrated_bit', 'ratchet_integrated_bit_image')]
    for comp_col, img_col in mapping_rules:
        if comp_col in df.columns and img_col in df.columns:
            for _, r in df.iterrows():
                nome, url = r[comp_col], r[img_col]
                if nome and nome != "n/a": img_map[nome] = url
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df, img_map

def get_img(url, size=(100, 100)):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join("images", f"{h}.png")
    if os.path.exists(path):
        img = Image.open(path)
        return img.resize(size, Image.Resampling.LANCZOS)
    return None

df_db, global_img_map = load_db()

# =========================
# SIDEBAR & SALVATAGGIO
# =========================
st.sidebar.title("👤 Account")
user_selected = st.sidebar.radio("Seleziona Utente:", ["Antonio", "Andrea", "Fabio"])
user_data = st.session_state.users[user_selected]

with st.sidebar:
    st.markdown("---")
    st.subheader("💾 Backup Dati")
    full_data_json = json.dumps(st.session_state.users, indent=2)
    st.download_button("Scarica Backup JSON", full_data_json, file_name="beyblade_backup.json")
    
    uploaded_file = st.file_uploader("Carica Backup", type="json")
    if uploaded_file is not None:
        st.session_state.users = json.load(uploaded_file)
        st.rerun()

# =========================
# UI PRINCIPALE
# =========================
st.markdown(f"<div class='user-title'>Officina di {user_selected}</div>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab1:
    search_q = st.text_input("Cerca...", "").lower()
    filtered = df_db[df_db['_search'].str.contains(search_q)] if search_q else df_db.head(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.markdown(f"<div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
            img = get_img(row['blade_image'] or row['beyblade_page_image'], size=(150, 150))
            if img: st.image(img)
            components = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"),
                          ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"),
                          ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                for ck, ik in components:
                    val = row[ck]
                    if val and val != "n/a": user_data["inv"][ik][val] = user_data["inv"][ik].get(val, 0) + 1
                st.rerun()
            st.markdown("<hr>", unsafe_allow_html=True)
            for ck, ik in components:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name-centered'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        user_data["inv"][ik][val] = user_data["inv"][ik].get(val, 0) + 1
                        st.rerun()

with tab2:
    modo = st.radio("Azione", ["Aggiungi (+1)", "Rimuovi (-1)"], horizontal=True)
    op = 1 if "Aggiungi" in modo else -1
    for cat, items in user_data["inv"].items():
        if items:
            with st.expander(cat.replace('_', ' ').upper()):
                for n, q in items.items():
                    if st.button(f"{n} x{q}", key=f"inv_{user_selected}_{cat}_{n}"):
                        user_data["inv"][cat][n] += op
                        if user_data["inv"][cat][n] <= 0: del user_data["inv"][cat][n]
                        st.rerun()

with tab3:
    def get_options(cat, theory=False):
        if theory:
            csv_map = {"lock_bit": "lock_chip", "blade": "blade", "main_blade": "main_blade", "assist_blade": "assist_blade", "ratchet": "ratchet", "bit": "bit", "ratchet_integrated_bit": "ratchet_integrated_bit"}
            return ["-"] + sorted([x for x in df_db[csv_map.get(cat, cat)].unique().tolist() if x and x != "n/a"])
        return ["-"] + sorted(list(user_data["inv"][cat].keys()))

    tipologie = ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", "BX/UX Theory", "CX Theory", "BX/UX+RIB Theory", "CX+RIB Theory"]

    for d_idx, deck in enumerate(user_data["decks"]):
        with st.expander(f"{deck['name'].upper()}", expanded=True):
            for s_idx in range(3):
                sels = deck["slots"][str(s_idx)] if str(s_idx) in deck["slots"] else {}
                nome_parti = [v for v in sels.values() if v and v != "-"]
                titolo_slot = " ".join(nome_parti) if nome_parti else f"SLOT {s_idx+1}"
                exp_key = f"{user_selected}-{d_idx}-{s_idx}"
                
                with st.expander(titolo_slot.upper(), expanded=st.session_state.exp_state.get(exp_key, False)):
                    tipo = st.selectbox("Sistema", tipologie, key=f"t_{user_selected}_{d_idx}_{s_idx}")
                    is_t = "Theory" in tipo
                    curr = {}
                    if "BX/UX" in tipo and "+RIB" not in tipo:
                        curr['b'] = st.selectbox("Blade", get_options("blade", is_t), key=f"b_{exp_key}")
                        curr['r'] = st.selectbox("Ratchet", get_options("ratchet", is_t), key=f"r_{exp_key}")
                        curr['bi'] = st.selectbox("Bit", get_options("bit", is_t), key=f"bi_{exp_key}")
                    elif "CX" in tipo and "+RIB" not in tipo:
                        curr['lb'] = st.selectbox("Lock Bit", get_options("lock_bit", is_t), key=f"lb_{exp_key}")
                        curr['mb'] = st.selectbox("Main Blade", get_options("main_blade", is_t), key=f"mb_{exp_key}")
                        curr['ab'] = st.selectbox("Assist Blade", get_options("assist_blade", is_t), key=f"ab_{exp_key}")
                        curr['r'] = st.selectbox("Ratchet", get_options("ratchet", is_t), key=f"r_{exp_key}")
                        curr['bi'] = st.selectbox("Bit", get_options("bit", is_t), key=f"bi_{exp_key}")
                    # ... (Aggiungi qui le altre tipologie +RIB se necessario)

                    cols = st.columns(5)
                    for i, (k, v) in enumerate(curr.items()):
                        if v != "-":
                            img_obj = get_img(global_img_map.get(v), size=(100, 100))
                            if img_obj: cols[i].image(img_obj)

                    if deck["slots"].get(str(s_idx)) != curr:
                        deck["slots"][str(s_idx)] = curr
                        st.session_state.exp_state[exp_key] = True
                        st.rerun()

            c1, c2, _ = st.columns([0.2, 0.2, 0.6])
            if c1.button("📝 Rinomina", key=f"ren_{d_idx}"):
                st.session_state.edit_name_idx = f"{user_selected}_{d_idx}"
                st.rerun()
            if c2.button("🗑️ Elimina", key=f"del_{d_idx}", type="primary"):
                user_data["decks"].pop(d_idx)
                st.rerun()

    if st.button("➕ Nuovo Deck"):
        user_data["decks"].append({"name": f"DECK {len(user_data['decks'])+1}", "slots": {str(i): {} for i in range(3)}})
        st.rerun()