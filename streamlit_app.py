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
import streamlit.components.v1 as components

# =========================
# CONFIGURAZIONE & STILE (Originale)
# =========================
def inject_css():
    st.markdown("""
        <style>
        :root { color-scheme: dark; }
        .stApp { background-color: #0f172a; color: #f1f5f9; }
        
        /* Forza grigio scuro su barre di ricerca e input */
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
        .ai-response-area {
            background-color: #1e293b;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #334155;
            color: #f1f5f9;
            font-family: monospace;
            white-space: pre-wrap;
        }
        </style>
    """, unsafe_allow_html=True)

inject_css()

# =========================
# FUNZIONI MODULARI (Richieste)
# =========================
def read_local_file(filename):
    """Legge file locali con gestione encoding."""
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()
        except:
            try:
                with open(filename, "r", encoding="latin-1") as f:
                    return f.read()
            except:
                return f"[ERRORE: Impossibile leggere {filename}]"
    return f"[ATTENZIONE: File {filename} non trovato]"

def run_ai_strategy(api_key, context_data):
    """Gestisce la chiamata a Gemini per l'analisi."""
    genai.configure(api_key=api_key)
    # Selezione automatica modello robusta
    valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    target_model = next((m for m in valid_models if "gemini-1.5-flash" in m), 
                        next((m for m in valid_models if "gemini-1.5-pro" in m), 
                        valid_models[0] if valid_models else None))
    
    if not target_model:
        return "Errore: Nessun modello Gemini disponibile."

    model = genai.GenerativeModel(target_model)
    
    # Costruzione prompt (Logica originale)
    prompt = f"""
{context_data['base_prompt']}
### DOCUMENTAZIONE:
<REGOLAMENTO>{context_data['regolamento']}</REGOLAMENTO>
<WBO_GUIDE>{context_data['wbo_guide']}</WBO_GUIDE>
<META_DATA>{context_data['meta_data']}</META_DATA>
<INVENTARIO>{context_data['inv_json']}</INVENTARIO>
### INPUT:
Strategia: {context_data['tipo']}, Lancio: {context_data['lancio']}, Torneo: {context_data['torneo']}
Obbligatori: {context_data['obbl']}, Esclusi: {context_data['escl']}
"""
    response = model.generate_content(prompt)
    return response.text

# =========================
# GESTIONE DATI (Originale)
# =========================
BIN_ID = st.secrets.get("jsonbin_id", "")
API_KEY = st.secrets.get("jsonbin_api_key", "")
URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {"X-Master-Key": API_KEY, "Content-Type": "application/json"}

def load_cloud():
    try:
        req = requests.get(URL, headers=HEADERS)
        if req.status_code == 200: return req.json().get("record", {})
    except: pass
    return {"utenti": {}}

def save_cloud():
    try: requests.put(URL, json=st.session_state.app_data, headers=HEADERS)
    except: pass

if 'app_data' not in st.session_state:
    st.session_state.app_data = load_cloud()

# =========================
# LOGIN (Ripristinato Originale)
# =========================
st.sidebar.title("Login Utente")
utenti_esistenti = list(st.session_state.app_data["utenti"].keys())

if utenti_esistenti:
    utente_sel = st.sidebar.selectbox("Seleziona Utente", ["-- Seleziona --"] + utenti_esistenti)
    if utente_sel != "-- Seleziona --":
        st.session_state.current_user = utente_sel

nuovo_utente = st.sidebar.text_input("Crea nuovo utente")
if st.sidebar.button("Registra"):
    if nuovo_utente.strip() and nuovo_utente not in st.session_state.app_data["utenti"]:
        st.session_state.app_data["utenti"][nuovo_utente] = {
            "inv": {"Blade": {}, "Ratchet": {}, "Bit": {}},
            "decks": {"deck_list": []}
        }
        save_cloud()
        st.session_state.current_user = nuovo_utente
        st.rerun()

# =========================
# APP PRINCIPALE
# =========================
if 'current_user' in st.session_state:
    current_user = st.session_state.current_user
    user_data = st.session_state.app_data["utenti"][current_user]
    
    st.markdown(f"<div class='user-title'>👤 {current_user}</div>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Inventario", "➕ Aggiungi", "🛠️ Deck Builder", "🤖 AI Advisor"])

    # --- TAB 1: INVENTARIO ---
    with tab1:
        st.markdown("### 📦 Inventario")
        inv_list = []
        for cat, items in user_data["inv"].items():
            for n, q in items.items(): inv_list.append({"Categoria": cat, "Pezzo": n, "Qta": q})
        
        if inv_list:
            st.dataframe(pd.DataFrame(inv_list), use_container_width=True, hide_index=True)
            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1: c_edit = st.selectbox("Cat.", ["Blade", "Ratchet", "Bit"])
            with col_e2: 
                p_lista = list(user_data["inv"][c_edit].keys())
                p_edit = st.selectbox("Pezzo", p_lista if p_lista else ["-"])
            with col_e3: q_edit = st.number_input("Qta", min_value=0, value=user_data["inv"][c_edit].get(p_edit, 1) if p_edit != "-" else 1)
            
            if st.button("Aggiorna/Rimuovi"):
                if p_edit != "-":
                    if q_edit <= 0: 
                        del user_data["inv"][c_edit][p_edit]
                        st.toast("🗑️ Pezzo rimosso")
                    else: 
                        user_data["inv"][c_edit][p_edit] = q_edit
                        st.toast("✅ Quantità aggiornata")
                    save_cloud()
                    time.sleep(1)
                    st.rerun()
        else: st.info("Inventario vuoto.")

    # --- TAB 2: AGGIUNGI (INTOCCABILE) ---
    with tab2:
        st.markdown("### ➕ Aggiungi Componenti")
        with st.form("add_form"):
            c_add = st.selectbox("Categoria", ["Blade", "Ratchet", "Bit"])
            n_add = st.text_input("Nome")
            q_add = st.number_input("Quantità", min_value=1, value=1)
            if st.form_submit_button("Aggiungi"):
                if n_add.strip():
                    name = n_add.strip()
                    user_data["inv"][c_add][name] = user_data["inv"][c_add].get(name, 0) + q_add
                    save_cloud()
                    st.success(f"Aggiunto {q_add}x {name}")
                else: st.error("Inserisci un nome.")

    # --- TAB 3: DECK BUILDER ---
    with tab3:
        st.markdown("### 🛠️ Builder 3v3")
        with st.container(border=True):
            d_name = st.text_input("Nome Deck")
            opts = {c: ["-"] + sorted(user_data["inv"][c].keys()) for c in ["Blade", "Ratchet", "Bit"]}
            
            s1 = [st.selectbox(f"{k} 1", opts[k]) for k in ["Blade", "Ratchet", "Bit"]]
            s2 = [st.selectbox(f"{k} 2", opts[k]) for k in ["Blade", "Ratchet", "Bit"]]
            s3 = [st.selectbox(f"{k} 3", opts[k]) for k in ["Blade", "Ratchet", "Bit"]]
            
            if st.button("Salva Deck"):
                user_data["decks"]["deck_list"].append({
                    "name": d_name,
                    "slots": [{"blade": x[0], "ratchet": x[1], "bit": x[2]} for x in [s1, s2, s3]]
                })
                save_cloud()
                st.toast("✅ Deck salvato!")
                time.sleep(1)
                st.rerun()

        for i, dk in enumerate(user_data["decks"]["deck_list"]):
            with st.expander(f"Deck: {dk['name']}"):
                for j, sl in enumerate(dk['slots']):
                    st.write(f"Slot {j+1}: {sl['blade']} - {sl['ratchet']} - {sl['bit']}")
                if st.button("Elimina Deck", key=f"del_{i}"):
                    user_data["decks"]["deck_list"].pop(i)
                    save_cloud()
                    st.toast("🗑️ Deck eliminato")
                    time.sleep(1)
                    st.rerun()

    # --- TAB 4: AI ADVISOR (Modularizzata) ---
    with tab4:
        st.markdown("### 🤖 AI Advisor")
        api_ai = st.secrets.get("gemini_api_key")
        if not api_ai: st.error("Manca API Key")
        else:
            with st.container(border=True):
                inv_flat = []
                for c in user_data["inv"]: inv_flat.extend(user_data["inv"][c].keys())
                
                col1, col2 = st.columns(2)
                with col1:
                    t_ai = st.selectbox("Approccio", ["Aggro", "Stamina", "Anti-meta", "Equilibrato"])
                    l_ai = st.slider("Lancio", 1, 10, 5)
                with col2:
                    o_ai = st.multiselect("Obbligatori", list(set(inv_flat)))
                    e_ai = st.multiselect("Evitare", list(set(inv_flat)))
                
                if st.button("Genera Analisi"):
                    with st.spinner("Analisi in corso..."):
                        ctx = {
                            "base_prompt": read_local_file("promptIA.txt"),
                            "regolamento": read_local_file("Regolamenti IBNA.txt"),
                            "wbo_guide": read_local_file("WBO Winning Combinations.txt"),
                            "meta_data": read_local_file("meta.txt"),
                            "inv_json": json.dumps(user_data["inv"]),
                            "tipo": t_ai, "lancio": l_ai, "torneo": "Competitivo",
                            "obbl": ", ".join(o_ai), "escl": ", ".join(e_ai)
                        }
                        st.session_state.ai_report = run_ai_strategy(api_ai, ctx)

            if 'ai_report' in st.session_state:
                st.markdown(f"<div class='ai-response-area'>{st.session_state.ai_report}</div>", unsafe_allow_html=True)
                
                # Importazione Deck (Originale)
                match = re.search(r'\{[\s\n]*"slots"[\s\n]*:[\s\S]*\}', st.session_state.ai_report, re.DOTALL)
                if match:
                    try:
                        ext_json = json.loads(match.group(0))
                        if st.button("Importa Deck AI"):
                            user_data["decks"]["deck_list"].append({
                                "name": f"AI_{t_ai}_{datetime.now().strftime('%d%m')}",
                                "slots": ext_json["slots"]
                            })
                            save_cloud()
                            st.toast("🚀 Deck importato!")
                            time.sleep(1)
                            st.rerun()
                    except: pass
else:
    st.warning("Seleziona o crea un utente nella barra laterale.")