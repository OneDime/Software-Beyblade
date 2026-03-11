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
import google.generativeai as genai

# =========================
# CONFIGURAZIONE & STILE
# =========================
def inject_css():
    st.markdown("""
        <style>
        :root { color-scheme: dark; }
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

st.set_page_config(page_title="Officina Beyblade X", layout="wide", initial_sidebar_state="expanded")
inject_css()

# =========================
# LOGICA GITHUB & AI (AUTO-REPAIR MODEL)
# =========================
GITHUB_TOKEN = st.secrets["github_token"]
REPO = st.secrets["github_repo"]
GEMINI_KEY = st.secrets.get("gemini_api_key")
FILES = {"inv": "inventario.json", "decks": "decks.json"}

def get_working_model():
    if not GEMINI_KEY: return None
    genai.configure(api_key=GEMINI_KEY)
    try:
        # Tenta di elencare i modelli e selezionare quello supportato dall'account
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5-flash' in m.name:
                    return genai.GenerativeModel(m.name)
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

model_engine = get_working_model()

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
            payload = {"message": f"Update {FILES[file_key]}", "content": base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8'), "sha": sha}
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
    if github_action("inv", inv_data, "PUT") and github_action("decks", deck_data, "PUT"):
        st.toast("✅ Dati salvati!", icon="💾")
    else: st.error("❌ Errore sincronizzazione")

if 'users' not in st.session_state:
    force_load()

# =========================
# DATABASE E LOGIN
# =========================
valid_users = ["Antonio", "Andrea", "Fabio"]
if 'user_sel' not in st.session_state:
    @st.dialog("Accesso Officina")
    def user_dialog():
        st.write("Seleziona utente:")
        for u in valid_users:
            if st.button(u, use_container_width=True):
                st.session_state.user_sel = u
                force_load(); st.rerun()
    user_dialog(); st.stop()

@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame(), {}, {}
    df = pd.read_csv("beyblade_x.csv").fillna("")
    img_map = {}
    theory_opts = {}
    mapping = [('lock_chip', 'lock_chip_image', 'lock_bit'), ('blade', 'blade_image', 'blade'), 
               ('main_blade', 'main_blade_image', 'main_blade'), ('assist_blade', 'assist_blade_image', 'assist_blade'), 
               ('ratchet', 'ratchet_image', 'ratchet'), ('bit', 'bit_image', 'bit'), 
               ('ratchet_integrated_bit', 'ratchet_integrated_bit_image', 'ratchet_integrated_bit')]
    for csv_col, img_col, state_key in mapping:
        if csv_col in df.columns:
            theory_opts[state_key] = ["-"] + sorted([x for x in df[csv_col].unique().tolist() if x and x != "n/a"])
            if img_col in df.columns:
                for _, r in df.iterrows():
                    if r[csv_col] and r[csv_col] != "n/a": img_map[r[csv_col]] = r[img_col]
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

df_db, global_img_map, theory_opts = load_db()
user_sel = st.session_state.user_sel
user_data = st.session_state.users[user_sel]

# Sidebar
st.sidebar.title(f"👤 {user_sel}")
if st.sidebar.button("Esci / Cambia Utente"):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder", "🤖 AI Advisor"])

# --- TAB 1: AGGIUNGI (INTOCCABILE) ---
with tab1:
    search_q = st.text_input("Cerca Beyblade...", "").lower()
    filtered = df_db[df_db['_search'].str.contains(search_q)] if search_q else df_db.head(10)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.expander(f"**{row['name'].upper()}**"):
            with st.container(border=True):
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

# --- TAB 2: INVENTARIO (INTOCCABILE) ---
with tab2:
    modo = st.radio("Azione", ["Aggiungi (+1)", "Rimuovi (-1)"], horizontal=True)
    op = 1 if "Aggiungi" in modo else -1
    for cat, items in user_data["inv"].items():
        if items:
            with st.expander(cat.replace('_', ' ').upper()):
                for n in sorted(list(items.keys())):
                    if st.button(f"{n} x{items[n]}", key=f"inv_{user_sel}_{cat}_{n}"):
                        user_data["inv"][cat][n] += op
                        if user_data["inv"][cat][n] <= 0: del user_data["inv"][cat][n]
                        save_cloud(); st.rerun()

# --- TAB 3: DECK BUILDER (INTOCCABILE) ---
with tab3:
    inv_opts = {cat: (["-"] + sorted(list(items.keys()))) for cat, items in user_data["inv"].items()}
    tipologie = ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", "BX/UX Theory", "CX Theory", "BX/UX+RIB Theory", "CX+RIB Theory"]
    for d_idx, deck in enumerate(user_data["decks"]):
        all_selected = []
        for s in deck["slots"].values():
            all_selected.extend([v for k, v in s.items() if v and v != "-" and k != "tipo"])
        with st.expander(deck['name'].upper(), expanded=False):
            for s_idx in range(3):
                curr = deck["slots"].get(str(s_idx), {})
                tipo_sys = curr.get("tipo", "BX/UX")
                keys_order = ["lb", "mb", "ab", "rib"] if "+RIB" in tipo_sys else (["lb", "mb", "ab", "r", "bi"] if "CX" in tipo_sys else ["b", "r", "bi"])
                if "+RIB" in tipo_sys and "BX/UX" in tipo_sys: keys_order = ["b", "rib"]
                titolo_base = [curr.get(k) for k in keys_order if curr.get(k) and curr.get(k) != "-"]
                nome_bey = " ".join(titolo_base).strip() or f"Slot {s_idx+1} Vuoto"
                ha_duplicati = any(all_selected.count(p) > 1 for p in titolo_base)
                alert_html = f"<span class='slot-summary-alert'>⚠️ DUPLICATO</span>" if ha_duplicati else ""
                st.markdown(f"<div class='slot-summary-box'><span class='slot-summary-name'>{nome_bey}</span>{alert_html}</div>", unsafe_allow_html=True)
            st.markdown("<hr>", unsafe_allow_html=True)
            for s_idx in range(3):
                s_key = str(s_idx); curr = deck["slots"].setdefault(s_key, {"tipo": "BX/UX"})
                with st.expander(f"SLOT {s_idx+1}"):
                    old_t = curr.get("tipo", "BX/UX")
                    tipo = st.selectbox("Sistema", tipologie, index=tipologie.index(old_t), key=f"t_{user_sel}_{d_idx}_{s_idx}")
                    if tipo != old_t: curr["tipo"] = tipo; st.rerun()
                    is_th = "Theory" in tipo
                    def update_comp(label, cat, k_comp):
                        opts = theory_opts[cat] if is_th else inv_opts[cat]
                        cur_v = curr.get(k_comp, "-")
                        if cur_v not in opts: cur_v = "-"
                        d_label = f"{label} ⚠️" if cur_v != "-" and all_selected.count(cur_v) > 1 else label
                        res = st.selectbox(d_label, opts, index=opts.index(cur_v), key=f"sel_{k_comp}_{user_sel}_{d_idx}_{s_idx}")
                        if curr.get(k_comp) != res: curr[k_comp] = res; st.rerun()
                    if "BX/UX" in tipo and "+RIB" not in tipo:
                        update_comp("Blade", "blade", "b"); update_comp("Ratchet", "ratchet", "r"); update_comp("Bit", "bit", "bi")
                    elif "CX" in tipo and "+RIB" not in tipo:
                        update_comp("Lock Bit", "lock_bit", "lb"); update_comp("Main Blade", "main_blade", "mb"); update_comp("Assist Blade", "assist_blade", "ab"); update_comp("Ratchet", "ratchet", "r"); update_comp("Bit", "bit", "bi")
                    elif "+RIB" in tipo:
                        if "CX" in tipo: update_comp("Lock Bit", "lock_bit", "lb"); update_comp("Main Blade", "main_blade", "mb"); update_comp("Assist Blade", "assist_blade", "ab")
                        else: update_comp("Blade", "blade", "b")
                        update_comp("RIB", "ratchet_integrated_bit", "rib")
            if st.button("Salva Deck", key=f"s_{user_sel}_{d_idx}"): save_cloud()

# --- TAB 4: AI ADVISOR (LAVORO ATTIVO QUI) ---
with tab4:
    st.markdown("### 🤖 Strategia Meta-Analitica WBO")
    
    if not GEMINI_KEY:
        st.error("⚠️ Chiave API Gemini non trovata.")
    else:
        with st.container(border=True):
            col_a, col_b = st.columns(2)
            with col_a:
                tipo_deck_ai = st.selectbox("🎯 Approccio", ["Aggro puro", "Anti-meta", "Stamina", "Difensivo", "Top meta", "Equilibrato"])
                lancio_ai = st.select_slider("🎯 Lancio (1-10)", options=list(range(1, 11)), value=5)
                # RIPRISTINATO: Selettore Torneo
                torneo_ai = st.selectbox("🎯 Tipo di Torneo", ["Locale / Amichevole", "Regionale", "Nazionale", "WBO Competitivo"])
            with col_b:
                all_owned = ["nessuna"]
                for cat in user_data["inv"]: all_owned.extend(sorted(user_data["inv"][cat].keys()))
                comp_obbl = st.selectbox("✅ Obbligatoria", all_owned)
                comp_escl = st.selectbox("❌ Escludi", all_owned)
            
            if st.button("🚀 GENERA ANALISI COMPETITIVA", use_container_width=True):
                with st.spinner("Interrogando il database WBO..."):
                    try:
                        # 1. Pulizia Meta CSV (Solo colonne richieste)
                        if os.path.exists("meta.csv"):
                            m_df = pd.read_csv("meta.csv", encoding='latin-1')
                            m_df.columns = m_df.columns.str.strip()
                            col_sel = ["Lock Chip", "Blade", "Assist Blade", "Ratchet", "Bit", "Points", "Sample Size (Win Count)", "Combo Rank", "Rank Change"]
                            meta_context = m_df[[c for c in col_sel if c in m_df.columns]].head(150).to_csv(index=False)
                        else: meta_context = "Meta non disponibile."

                        # 2. Prompt
                        inv_json = json.dumps(user_data["inv"], indent=2)
                        full_prompt = f"""Analizza i dati WBO: {meta_context}. 
                        Usa ESCLUSIVAMENTE l'inventario: {inv_json}. 
                        Parametri: Approccio {tipo_deck_ai}, Torneo {torneo_ai}, Lancio {lancio_ai}/10. 
                        Obbligatorio: {comp_obbl}. Escludi: {comp_escl}. 
                        Genera un report su Deck (3 combo), Matchup vs i Rank più alti e angoli di lancio."""

                        # 3. Generazione
                        response = model_engine.generate_content(full_prompt)
                        st.session_state.ai_report = response.text
                    except Exception as e:
                        st.error(f"Errore: {str(e)}")

        if 'ai_report' in st.session_state:
            st.markdown(f"<div class='ai-response-area'>{st.session_state.ai_report}</div>", unsafe_allow_html=True)