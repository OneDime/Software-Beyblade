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
# CONFIGURAZIONE & STILE
# =========================
st.set_page_config(page_title="Beyblade X Tracker", layout="wide", initial_sidebar_state="expanded")

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
# GESTIONE DATI & CLOUD
# =========================
BIN_ID = st.secrets.get("jsonbin_id", "")
API_KEY = st.secrets.get("jsonbin_api_key", "")
URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {
    "X-Master-Key": API_KEY,
    "Content-Type": "application/json"
}

def load_cloud():
    if not BIN_ID or not API_KEY:
        return {}
    try:
        req = requests.get(URL, headers=HEADERS)
        if req.status_code == 200:
            return req.json().get("record", {})
    except:
        pass
    return {}

def save_cloud():
    if not BIN_ID or not API_KEY:
        return
    try:
        requests.put(URL, json=st.session_state.app_data, headers=HEADERS)
    except:
        pass

if 'app_data' not in st.session_state:
    cloud_data = load_cloud()
    if not cloud_data:
        cloud_data = {"utenti": {}}
    st.session_state.app_data = cloud_data


# =========================
# MODULARIZZAZIONE FUNZIONI CORE
# =========================
def read_local_file(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            try:
                with open(filename, "r", encoding="latin-1") as f:
                    return f.read()
            except:
                return f"[ERRORE CRITICO: Impossibile leggere {filename}]"
    return f"[ATTENZIONE: File {filename} non trovato]"

def extract_json_from_text(text):
    match = re.search(r'\{[\s\n]*"slots"[\s\n]*:[\s\S]*\}', text, re.DOTALL)
    if match:
        try:
            raw_json = match.group(0)
            raw_json = raw_json[:raw_json.rfind('}')+1]
            return json.loads(raw_json)
        except:
            pass
    return None

def generate_ai_analysis(api_key, tipo_deck_ai, lancio_ai, torneo_ai, comp_obbl, comp_escl, user_data):
    genai.configure(api_key=api_key)
    valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    target_model = None
    for m in valid_models:
        if "gemini-1.5-flash" in m:
            target_model = m
            break
    if not target_model:
        for m in valid_models:
            if "gemini-1.5-pro" in m:
                target_model = m
                break
    if not target_model and valid_models:
        target_model = valid_models[0]
    
    if not target_model:
        raise Exception("Nessun modello compatibile trovato per questa API Key.")

    model = genai.GenerativeModel(target_model)

    base_prompt = read_local_file("promptIA.txt")
    regolamento = read_local_file("Regolamenti IBNA.txt")
    wbo_guide = read_local_file("WBO Winning Combinations.txt")
    meta_data = read_local_file("meta.txt") 

    if "[ERRORE" in base_prompt or "[ATTENZIONE" in base_prompt:
        raise Exception("File 'promptIA.txt' mancante o illeggibile.")

    inv_json = json.dumps(user_data["inv"], indent=2, ensure_ascii=False)
    obbl_str = ", ".join(comp_obbl) if comp_obbl else "Nessuna"
    escl_str = ", ".join(comp_escl) if comp_escl else "Nessuna"

    prompt_completo = f"""
{base_prompt}

### DOCUMENTAZIONE TECNICA DI RIFERIMENTO:
<REGOLAMENTO_IBNA>
{regolamento}
</REGOLAMENTO_IBNA>

<GUIDA_METAGAME_WBO>
{wbo_guide}
</GUIDA_METAGAME_WBO>

<DATI_STATISTICI_META>
{meta_data}
</DATI_STATISTICI_META>

<INVENTARIO_GIOCATORE>
{inv_json}
</INVENTARIO_GIOCATORE>

### INPUT SPECIFICI UTENTE:
- STRATEGIA DESIDERATA: {tipo_deck_ai}
- LIVELLO DI LANCIO: {lancio_ai}/10
- CONTESTO TORNEO: {torneo_ai}
- PEZZI RICHIESTI: {obbl_str}
- PEZZI BANDITI: {escl_str}

Esegui l'analisi e proponi la combinazione migliore basandoti sui dati statistici del file meta.txt e la disponibilità dei pezzi.
"""
    response = model.generate_content(prompt_completo)
    return response.text


# =========================
# LOGIN UTENTE
# =========================
st.sidebar.title("Login Utente")
utenti_esistenti = list(st.session_state.app_data["utenti"].keys())

if utenti_esistenti:
    utente_sel = st.sidebar.selectbox("Seleziona Utente", ["-- Seleziona --"] + utenti_esistenti)
else:
    utente_sel = "-- Seleziona --"
    st.sidebar.info("Nessun utente trovato. Creane uno nuovo.")

nuovo_utente = st.sidebar.text_input("Oppure crea nuovo utente")
if st.sidebar.button("Crea/Accedi"):
    user_to_login = nuovo_utente.strip() if nuovo_utente.strip() else (utente_sel if utente_sel != "-- Seleziona --" else None)
    if user_to_login:
        if user_to_login not in st.session_state.app_data["utenti"]:
            st.session_state.app_data["utenti"][user_to_login] = {
                "inv": {"Blade": {}, "Ratchet": {}, "Bit": {}},
                "decks": {"deck_list": []}
            }
            save_cloud()
        st.session_state.current_user = user_to_login
        st.rerun()

# =========================
# APP PRINCIPALE
# =========================
if 'current_user' in st.session_state:
    current_user = st.session_state.current_user
    user_data = st.session_state.app_data["utenti"][current_user]
    
    st.markdown(f"<div class='user-title'>👤 Benvenuto, {current_user}</div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📦 Inventario", "➕ Aggiungi", "🛠️ Deck Builder", "🤖 AI Advisor"])

    # --- TAB 1: INVENTARIO ---
    with tab1:
        st.markdown("### 📦 Il tuo Inventario")
        
        dati_inv = []
        for cat, items in user_data["inv"].items():
            for nome, qta in items.items():
                dati_inv.append({"Categoria": cat, "Nome": nome, "Quantità": qta})
        
        if dati_inv:
            df_inv = pd.DataFrame(dati_inv)
            st.dataframe(df_inv, use_container_width=True, hide_index=True)
            
            st.markdown("#### Gestione Rapida")
            col_del1, col_del2, col_del3 = st.columns(3)
            with col_del1:
                cat_edit = st.selectbox("Categoria", ["Blade", "Ratchet", "Bit"], key="cat_edit")
            with col_del2:
                pezzi_disp = list(user_data["inv"].get(cat_edit, {}).keys())
                nome_edit = st.selectbox("Pezzo", pezzi_disp if pezzi_disp else ["Nessuno"], key="nome_edit")
            with col_del3:
                if nome_edit != "Nessuno":
                    qta_attuale = user_data["inv"][cat_edit][nome_edit]
                    nuova_qta = st.number_input("Nuova Quantità", min_value=0, value=qta_attuale, step=1)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("💾 Aggiorna Quantità", use_container_width=True) and nome_edit != "Nessuno":
                    if nuova_qta == 0:
                        del user_data["inv"][cat_edit][nome_edit]
                        st.toast(f"🗑️ {nome_edit} rimosso dall'inventario")
                    else:
                        user_data["inv"][cat_edit][nome_edit] = nuova_qta
                        st.toast("✅ Quantità aggiornata")
                    save_cloud()
                    time.sleep(1)
                    st.rerun()
            with col_btn2:
                if st.button("🗑️ Rimuovi Pezzo", use_container_width=True) and nome_edit != "Nessuno":
                    del user_data["inv"][cat_edit][nome_edit]
                    save_cloud()
                    st.toast(f"🗑️ {nome_edit} eliminato")
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("L'inventario è vuoto. Aggiungi componenti dal tab 'Aggiungi'.")

    # --- TAB 2: AGGIUNGI ---
    with tab2:
        st.markdown("### ➕ Aggiungi Componenti")
        with st.form("form_aggiungi"):
            cat_add = st.selectbox("Categoria", ["Blade", "Ratchet", "Bit"])
            nome_add = st.text_input("Nome Componente")
            qta_add = st.number_input("Quantità", min_value=1, value=1, step=1)
            
            submitted = st.form_submit_button("Aggiungi all'Inventario")
            if submitted:
                if nome_add.strip() == "":
                    st.error("Inserisci un nome valido.")
                else:
                    nome_pulito = nome_add.strip()
                    if nome_pulito in user_data["inv"][cat_add]:
                        user_data["inv"][cat_add][nome_pulito] += qta_add
                    else:
                        user_data["inv"][cat_add][nome_pulito] = qta_add
                    save_cloud()
                    st.success(f"Aggiunto: {qta_add}x {nome_pulito} ({cat_add})")

    # --- TAB 3: DECK BUILDER ---
    with tab3:
        st.markdown("### 🛠️ Costruisci il tuo Deck 3v3")
        
        with st.container(border=True):
            nome_deck_nuovo = st.text_input("Nome del Deck", placeholder="Es. WBO Aggro...")
            
            blades_disp = ["Nessuno"] + sorted(list(user_data["inv"]["Blade"].keys()))
            ratchets_disp = ["Nessuno"] + sorted(list(user_data["inv"]["Ratchet"].keys()))
            bits_disp = ["Nessuno"] + sorted(list(user_data["inv"]["Bit"].keys()))

            st.markdown("#### Slot 1")
            col1, col2, col3 = st.columns(3)
            with col1: b1 = st.selectbox("Blade 1", blades_disp, key="b1")
            with col2: r1 = st.selectbox("Ratchet 1", ratchets_disp, key="r1")
            with col3: bi1 = st.selectbox("Bit 1", bits_disp, key="bi1")
            
            st.markdown("#### Slot 2")
            col4, col5, col6 = st.columns(3)
            with col4: b2 = st.selectbox("Blade 2", blades_disp, key="b2")
            with col5: r2 = st.selectbox("Ratchet 2", ratchets_disp, key="r2")
            with col6: bi2 = st.selectbox("Bit 2", bits_disp, key="bi2")
            
            st.markdown("#### Slot 3")
            col7, col8, col9 = st.columns(3)
            with col7: b3 = st.selectbox("Blade 3", blades_disp, key="b3")
            with col8: r3 = st.selectbox("Ratchet 3", ratchets_disp, key="r3")
            with col9: bi3 = st.selectbox("Bit 3", bits_disp, key="bi3")

            if st.button("💾 Salva Deck", use_container_width=True):
                if not nome_deck_nuovo.strip():
                    st.error("Inserisci un nome per il deck.")
                else:
                    nuovo_deck = {
                        "name": nome_deck_nuovo.strip(),
                        "slots": [
                            {"blade": b1, "ratchet": r1, "bit": bi1},
                            {"blade": b2, "ratchet": r2, "bit": bi2},
                            {"blade": b3, "ratchet": r3, "bit": bi3}
                        ]
                    }
                    user_data["decks"]["deck_list"].append(nuovo_deck)
                    save_cloud()
                    st.toast(f"✅ Deck '{nome_deck_nuovo}' salvato con successo!")
                    time.sleep(1)
                    st.rerun()

        st.markdown("---")
        st.markdown("### 📋 I tuoi Deck Salvati")
        
        if not user_data["decks"]["deck_list"]:
            st.info("Nessun deck salvato.")
        else:
            for idx, deck in enumerate(user_data["decks"]["deck_list"]):
                with st.expander(f"🗡️ {deck['name']}"):
                    for i, slot in enumerate(deck["slots"]):
                        st.write(f"**Slot {i+1}:** {slot.get('blade','Nessuno')} | {slot.get('ratchet','Nessuno')} | {slot.get('bit','Nessuno')}")
                    if st.button("🗑️ Elimina", key=f"del_deck_{idx}"):
                        user_data["decks"]["deck_list"].pop(idx)
                        save_cloud()
                        st.toast("🗑️ Deck eliminato")
                        time.sleep(1)
                        st.rerun()

    # --- TAB 4: AI ADVISOR ---
    with tab4:
        st.markdown("### 🤖 Strategia Meta-Analitica WBO")
        
        API_KEY_AI = st.secrets.get("gemini_api_key")
        if not API_KEY_AI:
            st.error("⚠️ Chiave API mancante in secrets.")
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
                    with st.spinner("Inizializzazione AI e lettura file..."):
                        try:
                            report_text = generate_ai_analysis(
                                API_KEY_AI, tipo_deck_ai, lancio_ai, torneo_ai, comp_obbl, comp_escl, user_data
                            )
                            st.session_state.ai_report = report_text
                        except Exception as e:
                            st.error(f"Errore tecnico: {str(e)}")

            if 'ai_report' in st.session_state:
                st.markdown(f"<div class='ai-response-area'>{st.session_state.ai_report}</div>", unsafe_allow_html=True)
                
                extracted_json = extract_json_from_text(st.session_state.ai_report)
                
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
                            nome_deck = f"{tipo_deck_ai}_{datetime.now().strftime('%d/%m/%Y')}"
                            nuovo_deck = {"name": nome_deck, "slots": extracted_json["slots"]}
                            user_data["decks"]["deck_list"].append(nuovo_deck)
                            save_cloud()
                            st.toast(f"🚀 Deck '{nome_deck}' importato con successo!")
                            time.sleep(1.5)
                            st.rerun()
                    else:
                        st.info("ℹ️ Nessun deck pronto per l'importazione automatica.")

else:
    st.warning("👈 Effettua il login o crea un utente dalla barra laterale per iniziare.")