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
# LOGICA GITHUB
# =========================
GITHUB_TOKEN = st.secrets["github_token"]
REPO = st.secrets["github_repo"]
# AGGIUNTO SOLO IL FILE STATS
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
    st.query_params.clear()
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()
if st.sidebar.button("🔄 Forza Sync Cloud"):
    force_load(); st.rerun()

if 'edit_name_idx' not in st.session_state: st.session_state.edit_name_idx = None

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder", "🤖 AI Advisor", "📊 Registro Match"])

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
                
                if "CX" in tipo_sys:
                    keys_order = ["lb", "mb", "ab", "rib"] if "+RIB" in tipo_sys else ["lb", "mb", "ab", "r", "bi"]
                else:
                    keys_order = ["b", "rib"] if "+RIB" in tipo_sys else ["b", "r", "bi"]
                
                titolo_base = [curr.get(k) for k in keys_order if curr.get(k) and curr.get(k) != "-"]
                nome_bey = " ".join(titolo_base).strip() or f"Slot {s_idx+1} Vuoto"
                ha_duplicati = any(all_selected.count(p) > 1 for p in titolo_base)
                alert_html = f"<span class='slot-summary-alert'>⚠️ DUPLICATO</span>" if ha_duplicati else ""
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
                        curr["tipo"] = tipo; st.rerun()

                    is_th = "Theory" in tipo
                    def update_comp(label, cat, k_comp):
                        opts = theory_opts[cat] if is_th else inv_opts[cat]
                        current_val = curr.get(k_comp, "-")
                        if current_val not in opts: current_val = "-"
                        display_label = f"{label} ⚠️" if current_val != "-" and all_selected.count(current_val) > 1 else label
                        res = st.selectbox(display_label, opts, index=opts.index(current_val), key=f"sel_{k_comp}_{user_sel}_{d_idx}_{s_idx}")
                        if curr.get(k_comp) != res:
                            curr[k_comp] = res; st.rerun()

                    if "BX/UX" in tipo and "+RIB" not in tipo:
                        update_comp("Blade", "blade", "b"); update_comp("Ratchet", "ratchet", "r"); update_comp("Bit", "bit", "bi")
                        k_img_order = ["b", "r", "bi"]
                    elif "CX" in tipo and "+RIB" not in tipo:
                        update_comp("Lock Bit", "lock_bit", "lb"); update_comp("Main Blade", "main_blade", "mb"); update_comp("Assist Blade", "assist_blade", "ab"); update_comp("Ratchet", "ratchet", "r"); update_comp("Bit", "bit", "bi")
                        k_img_order = ["lb", "mb", "ab", "r", "bi"]
                    elif "+RIB" in tipo:
                        if "CX" in tipo:
                            update_comp("Lock Bit", "lock_bit", "lb"); update_comp("Main Blade", "main_blade", "mb"); update_comp("Assist Blade", "assist_blade", "ab")
                            k_img_order = ["lb", "mb", "ab", "rib"]
                        else: 
                            update_comp("Blade", "blade", "b")
                            k_img_order = ["b", "rib"]
                        update_comp("RIB", "ratchet_integrated_bit", "rib")

                    st.write("") 
                    cols = st.columns(5)
                    col_idx = 0
                    for k in k_img_order:
                        v = curr.get(k)
                        if v and v != "-":
                            img_obj = get_img(global_img_map.get(v))
                            if img_obj: cols[col_idx].image(img_obj, width=80); col_idx += 1

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

# --- TAB 4: AI ADVISOR (INTOCCABILE) ---
with tab4:
    st.markdown("### 🤖 Strategia Meta-Analitica WBO")
    
    API_KEY = st.secrets.get("gemini_api_key")
    if not API_KEY:
        st.error("⚠️ Chiave API mancante.")
    else:
        with st.container(border=True):
            tutti_pezzi = []
            for cat in user_data["inv"]:
                tutti_pezzi.extend(sorted(user_data["inv"][cat].keys()))
            tutti_pezzi = sorted(list(set(tutti_pezzi)))

            col_a, col_b = st.columns(2)
            with col_a:
                approcci = ["Aggro puro", "Anti-meta", "Stamina dominante", "Difensivo/Counter", "Top Meta ottimizzato", "Equilibrato", "High-risk High-reward", "Tech specialist"]
                tipo_deck_ai = st.selectbox("🎯 Approccio", approcci)
                lancio_ai = st.select_slider("🎯 Capacità di lancio (1-10)", options=list(range(1, 11)), value=5)
                torneo_ai = st.selectbox("🎯 Tipo di Torneo", ["Locale / Amichevole", "Regionale", "Nazionale", "WBO Competitivo"])
            
            with col_b:
                comp_obbl = st.multiselect("✅ Componenti Obbligatorie", tutti_pezzi)
                comp_escl = st.multiselect("❌ Componenti da evitare", tutti_pezzi)
            
            if st.button("🚀 GENERA ANALISI COMPETITIVA", use_container_width=True):
                with st.spinner("Ricerca modello e generazione analisi..."):
                    try:
                        genai.configure(api_key=API_KEY)
                        
                        try:
                            valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                            if any("gemini-1.5-flash" in m for m in valid_models):
                                target = next(m for m in valid_models if "gemini-1.5-flash" in m)
                            elif any("gemini-1.5-pro" in m for m in valid_models):
                                target = next(m for m in valid_models if "gemini-1.5-pro" in m)
                            else:
                                target = valid_models[0]
                            model = genai.GenerativeModel(target)
                        except Exception as e_mod:
                            st.error(f"Errore inizializzazione modelli: {e_mod}")
                            st.stop()

                        if os.path.exists("promptIA.txt"):
                            with open("promptIA.txt", "r", encoding="utf-8") as f:
                                base_prompt = f.read()
                        else:
                            st.error("File promptIA.txt non trovato.")
                            st.stop()

                        inv_json = json.dumps(user_data["inv"], indent=2, ensure_ascii=False)
                        obbl_str = ", ".join(comp_obbl) if comp_obbl else "nessuna"
                        escl_str = ", ".join(comp_escl) if comp_escl else "nessuna"

                        prompt_completo = f"""
{base_prompt}

### DATI GIOCATORE CORRENTI:
- INVENTARIO: {inv_json}
- APPROCCIO: {tipo_deck_ai}
- SKILL LANCIO: {lancio_ai}/10
- TIPO TORNEO: {torneo_ai}
- COMPONENTI OBBLIGATORIE: {obbl_str}
- COMPONENTI VIETATE: {escl_str}

Procedi con l'analisi tecnica rigorosa.
"""
                        response = model.generate_content(prompt_completo)
                        st.session_state.ai_report = response.text
                        
                    except Exception as e:
                        st.error(f"Errore critico: {str(e)}")

        if 'ai_report' in st.session_state:
            st.markdown(f"<div class='ai-response-area'>{st.session_state.ai_report}</div>", unsafe_allow_html=True)
            
            extracted_json = None
            match = re.search(r'\{[\s\n]*"slots"[\s\n]*:[\s\S]*\}', st.session_state.ai_report, re.DOTALL)
            if match:
                raw_json = match.group(0)
                raw_json = raw_json[:raw_json.rfind('}')+1]
                try:
                    extracted_json = json.loads(raw_json)
                except Exception as e:
                    pass
            
            col_dl, col_imp = st.columns(2)
            with col_dl:
                st.download_button(
                    label="📥 Scarica Report (.txt)",
                    data=st.session_state.ai_report,
                    file_name=f"Report_WBO_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col_imp:
                if extracted_json and "slots" in extracted_json:
                    if st.button("🚀 Importa Deck nel Builder", type="primary", use_container_width=True):
                        oggi_str = datetime.now().strftime('%d/%m/%Y')
                        nome_deck = f"{tipo_deck_ai}_{oggi_str}"
                        nuovo_deck = {"name": nome_deck, "slots": extracted_json["slots"]}
                        user_data["decks"].append(nuovo_deck)
                        save_cloud()
                        st.success(f"Deck '{nome_deck}' importato!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.info("⚠️ L'AI non ha fornito un JSON compatibile in questa run.")

# --- TAB 5: REGISTRO MATCH (LAVORAZIONE ESCLUSIVA) ---
with tab5:
    st.markdown("### 📊 Registro Rapido Scontri")
    
    if 'match_counter' not in st.session_state:
        st.session_state.match_counter = 0
    
    col_p1, col_p2 = st.columns(2)
    p_options = ["Antonio", "Andrea", "Fabio", "Esterno"]
    with col_p1: g1 = st.selectbox("Giocatore 1", p_options, index=p_options.index(user_sel) if user_sel in p_options else 0)
    with col_p2: g2 = st.selectbox("Giocatore 2", p_options, index=1 if user_sel != "Andrea" else 0)

    def get_bey_names(player_name, suffix):
        if player_name == "Esterno":
            with st.expander(f"⚙️ Configura Bey Esterni ({suffix})"):
                return [st.text_input(f"Bey {i+1} ({suffix})", f"Esterno {i+1}", key=f"ext_{suffix}_{i}") for i in range(3)]
        else:
            p_decks = st.session_state.users[player_name]["decks"]
            names = []
            for d in p_decks:
                for s_idx in range(3):
                    curr = d["slots"].get(str(s_idx), {})
                    tipo = curr.get("tipo", "BX/UX")
                    keys = ["lb", "mb", "ab", "r", "bi"] if "CX" in tipo else ["b", "r", "bi"]
                    if "+RIB" in tipo: keys = ["lb", "mb", "ab", "rib"] if "CX" in tipo else ["b", "rib"]
                    n = " ".join([curr.get(k) for k in keys if curr.get(k) and curr.get(k) != "-"]).strip()
                    if n: names.append(f"{d['name']} - {n}")
            return sorted(list(set(names))) if names else ["-"]

    beys_g1 = get_bey_names(g1, "G1")
    beys_g2 = get_bey_names(g2, "G2")
    punteggi = ["-", "1-0", "2-0", "3-0", "0-1", "0-2", "0-3"]

    df_init = pd.DataFrame(
        [{"Bey G1": "-", "Bey G2": "-", "Punti": "-"} for _ in range(7)],
        index=range(1, 8)
    )
    
    edited_df = st.data_editor(
        df_init,
        column_config={
            "Bey G1": st.column_config.SelectboxColumn("Bey G1", options=beys_g1, width="medium"),
            "Bey G2": st.column_config.SelectboxColumn("Bey G2", options=beys_g2, width="medium"),
            "Punti": st.column_config.SelectboxColumn("Punti", options=punteggi, width="small"),
        },
        use_container_width=True,
        key=f"match_editor_vFINAL_{st.session_state.match_counter}"
    )

    if st.button("🚀 SALVA MATCH NEL CLOUD", use_container_width=True, type="primary"):
        valid_rows = edited_df[edited_df["Punti"] != "-"]
        
        if valid_rows.empty:
            st.warning("Compila almeno un round.")
        else:
            # Salvataggio data limitato a gg/mm/aaaa
            now_str = datetime.now().strftime("%d/%m/%Y")
            new_records = []
            
            for _, row in valid_rows.iterrows():
                p1_raw, p2_raw = map(int, row["Punti"].split("-"))
                
                if p1_raw > p2_raw:
                    val_g1, val_g2 = p1_raw, -p1_raw
                else:
                    val_g1, val_g2 = -p2_raw, p2_raw
                
                b1_clean = row["Bey G1"].split(" - ", 1)[-1] if " - " in row["Bey G1"] else row["Bey G1"]
                b2_clean = row["Bey G2"].split(" - ", 1)[-1] if " - " in row["Bey G2"] else row["Bey G2"]
                
                new_records.append({
                    "Data": now_str,
                    "NomeGiocatore1": g1,
                    "BeyG1": b1_clean,
                    "NomeGiocatore2": g2,
                    "BeyG2": b2_clean,
                    "PunteggioBeyG1": val_g1,
                    "PunteggioBeyG2": val_g2
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
                    # Logica robusta per la data (sia vecchio che nuovo formato per evitare crash sui vecchi dati)
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
                    
                    # Generazione Punteggi Beyblade (Foglio 2)
                    df1 = df_history[['BeyG1', 'PunteggioBeyG1']].rename(columns={'BeyG1': 'Bey', 'PunteggioBeyG1': 'Score'})
                    df2 = df_history[['BeyG2', 'PunteggioBeyG2']].rename(columns={'BeyG2': 'Bey', 'PunteggioBeyG2': 'Score'})
                    
                    df_concat = pd.concat([df1, df2])
                    df_concat['Score'] = pd.to_numeric(df_concat['Score'], errors='coerce').fillna(0)
                    df_scores = df_concat.groupby('Bey')['Score'].sum().reset_index().sort_values(by='Score', ascending=False)
                    
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        # Foglio 1: match history
                        df_history.to_excel(writer, sheet_name='match history', index=False)
                        worksheet_history = writer.sheets['match history']
                        worksheet_history.autofilter(0, 0, len(df_history), len(df_history.columns) - 1)
                        
                        # Foglio 2: Punteggi Beyblade
                        df_scores.to_excel(writer, sheet_name='Punteggi Beyblade', index=False)
                        
                        # Fogli Utenti: Antonio, Andrea, Fabio
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