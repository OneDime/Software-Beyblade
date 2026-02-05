import streamlit as st
import pandas as pd
import hashlib
import os
import json
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# =========================
# CONFIGURAZIONE & STILE (INALTERATO)
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    
    /* TITOLO UTENTE PICCOLO */
    .user-title { font-size: 28px !important; font-weight: bold; margin-bottom: 20px; color: #f1f5f9; }

    /* STILI TAB AGGIUNGI (INTOCCABILI) */
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

    /* BOTTONI AGGIUNGI (INTOCCABILI) */
    div.stButton > button {
        width: auto !important; min-width: 150px !important;
        height: 30px !important; background-color: #334155 !important; color: white !important;
        border: 1px solid #475569 !important; border-radius: 4px !important;
    }

    /* STILE EXPANDER */
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; text-align: left !important; margin-bottom: 5px !important; }
    
    /* SIDEBAR CUSTOM */
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# LOGICA SALVATAGGIO (NUOVA E PROTETTA)
# =========================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1VW5TUbrvnHnSn9WCbmrkCfOgUo85et4jQK9pSgTrdkM/edit#gid=0"

def save_cloud():
    """Salva i dati su foglio senza interrompere l'app in caso di errore"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Preparazione dati per i due fogli
        inv_data = [{"Utente": u, "Dati_JSON": json.dumps(st.session_state.users[u]["inv"])} for u in st.session_state.users]
        deck_data = [{"Utente": u, "Dati_JSON": json.dumps(st.session_state.users[u]["decks"])} for u in st.session_state.users]
        
        conn.update(spreadsheet=SHEET_URL, worksheet="inventario", data=pd.DataFrame(inv_data))
        conn.update(spreadsheet=SHEET_URL, worksheet="decks", data=pd.DataFrame(deck_data))
    except:
        pass # Se fallisce, l'utente continua a giocare e il salvataggio riprova al prossimo click

def load_cloud():
    """Carica i dati iniziali dal foglio"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_i = conn.read(spreadsheet=SHEET_URL, worksheet="inventario", ttl=0)
        df_d = conn.read(spreadsheet=SHEET_URL, worksheet="decks", ttl=0)
        loaded = {}
        for u in ["Antonio", "Andrea", "Fabio"]:
            u_i = df_i[df_i["Utente"] == u]
            u_d = df_d[df_d["Utente"] == u]
            loaded[u] = {
                "inv": json.loads(u_i.iloc[0]["Dati_JSON"]) if not u_i.empty else {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]},
                "decks": json.loads(u_d.iloc[0]["Dati_JSON"]) if not u_d.empty else [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]
            }
        return loaded
    except:
        return None

# =========================
# LOGICA DATI & IMMAGINI (TUA)
# =========================
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

# =========================
# GESTIONE ACCOUNT (TUA + CARICAMENTO CLOUD)
# =========================
if 'users' not in st.session_state:
    cloud_data = load_cloud()
    if cloud_data:
        st.session_state.users = cloud_data
    else:
        st.session_state.users = {
            "Antonio": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]},
            "Andrea": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]},
            "Fabio": {"inv": {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}, "decks": [{"name": "DECK 1", "slots": {i: {} for i in range(3)}}]}
        }

st.sidebar.title("👤 Account")
user_selected = st.sidebar.radio("Seleziona Utente:", ["Antonio", "Andrea", "Fabio"])

user_data = st.session_state.users[user_selected]
inventario_corrente = user_data["inv"]
decks_correnti = user_data["decks"]

if 'exp_state' not in st.session_state: st.session_state.exp_state = {}
if 'edit_name_idx' not in st.session_state: st.session_state.edit_name_idx = None

df, global_img_map = load_db()

# =========================
# UI PRINCIPALE (LA TUA LOGICA INTEGRALE)
# =========================
st.markdown(f"<div class='user-title'>Officina di {user_selected}</div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab1:
    search_q = st.text_input("Cerca...", "").lower()
    filtered = df[df['_search'].str.contains(search_q)] if search_q else df.head(3)
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
                    if val and val != "n/a": inventario_corrente[ik][val] = inventario_corrente[ik].get(val, 0) + 1
                save_cloud() # SALVATAGGIO AUTO
                st.toast(f"Aggiunto a {user_selected}!")
            st.markdown("<hr>", unsafe_allow_html=True)
            for ck, ik in components:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name-centered'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        inventario_corrente[ik][val] = inventario_corrente[ik].get(val, 0) + 1
                        save_cloud() # SALVATAGGIO AUTO
                        st.toast(f"Aggiunto: {val}")

with tab2:
    modo = st.radio("L", ["Aggiungi (+1)", "Rimuovi (-1)"], horizontal=True, label_visibility="collapsed")
    operazione = 1 if "Aggiungi" in modo else -1
    for categoria, pezzi in inventario_corrente.items():
        if pezzi:
            with st.expander(categoria.replace('_', ' ').upper()):
                for nome, qta in pezzi.items():
                    if st.button(f"{nome} x{qta}", key=f"inv_{user_selected}_{categoria}_{nome}"):
                        inventario_corrente[categoria][nome] += operazione
                        if inventario_corrente[categoria][nome] <= 0: del inventario_corrente[categoria][nome]
                        save_cloud() # SALVATAGGIO AUTO
                        st.rerun()

with tab3:
    def get_options(cat, theory=False):
        if theory:
            csv_map = {"lock_bit": "lock_chip", "blade": "blade", "main_blade": "main_blade", "assist_blade": "assist_blade", "ratchet": "ratchet", "bit": "bit", "ratchet_integrated_bit": "ratchet_integrated_bit"}
            return ["-"] + sorted([x for x in df[csv_map.get(cat, cat)].unique().tolist() if x and x != "n/a"])
        return ["-"] + sorted(list(inventario_corrente[cat].keys()))

    tipologie = ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", "BX/UX Theory", "CX Theory", "BX/UX+RIB Theory", "CX+RIB Theory"]

    for d_idx, deck in enumerate(decks_correnti):
        with st.expander(f"{deck['name'].upper()}", expanded=True):
            for s_idx in range(3):
                sels = deck["slots"][s_idx]
                nome_parti = [v for v in sels.values() if v and v != "-"]
                titolo_slot = " ".join(nome_parti) if nome_parti else f"SLOT {s_idx+1}"
                exp_key = f"{user_selected}-{d_idx}-{s_idx}"
                with st.expander(titolo_slot.upper(), expanded=st.session_state.exp_state.get(exp_key, False)):
                    tipo = st.selectbox("Sistema", tipologie, key=f"type_{user_selected}_{d_idx}_{s_idx}")
                    is_theory = "Theory" in tipo
                    curr = {}
                    if "BX/UX" in tipo and "+RIB" not in tipo:
                        curr['b'] = st.selectbox("Blade", get_options("blade", is_theory), key=f"b_{user_selected}_{d_idx}_{s_idx}")
                        curr['r'] = st.selectbox("Ratchet", get_options("ratchet", is_theory), key=f"r_{user_selected}_{d_idx}_{s_idx}")
                        curr['bi'] = st.selectbox("Bit", get_options("bit", is_theory), key=f"bi_{user_selected}_{d_idx}_{s_idx}")
                    elif "CX" in tipo and "+RIB" not in tipo:
                        curr['lb'] = st.selectbox("Lock Bit", get_options("lock_bit", is_theory), key=f"lb_{user_selected}_{d_idx}_{s_idx}")
                        curr['mb'] = st.selectbox("Main Blade", get_options("main_blade", is_theory), key=f"mb_{user_selected}_{d_idx}_{s_idx}")
                        curr['ab'] = st.selectbox("Assist Blade", get_options("assist_blade", is_theory), key=f"ab_{user_selected}_{d_idx}_{s_idx}")
                        curr['r'] = st.selectbox("Ratchet", get_options("ratchet", is_theory), key=f"r_{user_selected}_{d_idx}_{s_idx}")
                        curr['bi'] = st.selectbox("Bit", get_options("bit", is_theory), key=f"bi_{user_selected}_{d_idx}_{s_idx}")
                    elif "BX/UX+RIB" in tipo:
                        curr['b'] = st.selectbox("Blade", get_options("blade", is_theory), key=f"b_{user_selected}_{d_idx}_{s_idx}")
                        curr['rib'] = st.selectbox("RIB", get_options("ratchet_integrated_bit", is_theory), key=f"rib_{user_selected}_{d_idx}_{s_idx}")
                    elif "CX+RIB" in tipo:
                        curr['lb'] = st.selectbox("Lock Bit", get_options("lock_bit", is_theory), key=f"lb_{user_selected}_{d_idx}_{s_idx}")
                        curr['mb'] = st.selectbox("Main Blade", get_options("main_blade", is_theory), key=f"mb_{user_selected}_{d_idx}_{s_idx}")
                        curr['ab'] = st.selectbox("Assist Blade", get_options("assist_blade", is_theory), key=f"ab_{user_selected}_{d_idx}_{s_idx}")
                        curr['rib'] = st.selectbox("RIB", get_options("ratchet_integrated_bit", is_theory), key=f"rib_{user_selected}_{d_idx}_{s_idx}")

                    st.write("")
                    cols = st.columns(5)
                    for i, (k, v) in enumerate(curr.items()):
                        if v != "-":
                            url = global_img_map.get(v)
                            img_obj = get_img(url, size=(100, 100))
                            if img_obj: cols[i].image(img_obj)

                    if deck["slots"][s_idx] != curr:
                        deck["slots"][s_idx] = curr
                        save_cloud() # SALVATAGGIO AUTO
                        st.session_state.exp_state[exp_key] = True
                        st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2, _ = st.columns([0.2, 0.2, 0.6])
            if c1.button("📝 Rinomina", key=f"ren_{user_selected}_{d_idx}"):
                st.session_state.edit_name_idx = f"{user_selected}_{d_idx}"
                st.rerun()
            if c2.button("🗑️ Elimina", key=f"del_{user_selected}_{d_idx}", type="primary"):
                if len(decks_correnti) > 1:
                    decks_correnti.pop(d_idx)
                    save_cloud() # SALVATAGGIO AUTO
                    st.rerun()
            if st.session_state.edit_name_idx == f"{user_selected}_{d_idx}":
                new_n = st.text_input("Nuovo nome:", deck['name'], key=f"input_{user_selected}_{d_idx}")
                if st.button("Salva", key=f"save_{user_selected}_{d_idx}"):
                    deck['name'] = new_n
                    save_cloud() # SALVATAGGIO AUTO
                    st.session_state.edit_name_idx = None
                    st.rerun()

    st.markdown("---")
    if st.button("➕ Aggiungi Nuovo Deck"):
        decks_correnti.append({"name": f"DECK {len(decks_correnti) + 1}", "slots": {i: {} for i in range(3)}})
        save_cloud() # SALVATAGGIO AUTO
        st.rerun()