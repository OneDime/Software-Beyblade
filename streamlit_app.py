import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* --- TAB AGGIUNGI (INTOCCABILE) --- */
    .add-container [data-testid="stVerticalBlock"] { text-align: center; align-items: center; }
    .add-container div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #334155 !important;
        background-color: #1e293b !important;
        border-radius: 12px !important;
        margin-bottom: 25px !important;
        padding: 15px !important;
    }
    .bey-name { font-weight: bold; font-size: 1.4rem; color: #60a5fa; text-transform: uppercase; margin-bottom: 8px; text-align: center; }
    .comp-name-centered { font-size: 1.1rem; color: #cbd5e1; margin-top: 5px; margin-bottom: 2px; text-align: center; width: 100%; display: block; }

    /* --- TAB INVENTARIO (SINISTRA) --- */
    [data-testid="stExpander"] [data-testid="stVerticalBlock"] { text-align: left !important; align-items: flex-start !important; }
    .inv-row-container { text-align: left !important; display: flex !important; flex-direction: column !important; align-items: flex-start !important; width: 100%; }
    .inv-row-container button { text-align: left !important; justify-content: flex-start !important; width: 100% !important; padding-left: 10px !important; background: transparent !important; border: none !important; }
    
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; }

    /* Bottone Elimina (Rosso) */
    div.stButton > button[key^="del_deck_"] { background-color: #991b1b !important; color: white !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# FUNZIONI & DATI
# =========================
@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame()
    df = pd.read_csv("beyblade_x.csv").fillna("")
    # Creiamo dizionari di lookup per le immagini per velocità
    img_map = {}
    cols_to_check = ['lock_chip', 'blade', 'main_blade', 'assist_blade', 'ratchet', 'bit', 'ratchet_integrated_bit']
    for col in cols_to_check:
        if col in df.columns:
            # Associa il nome del pezzo alla sua immagine (usa blade_image o beyblade_page_image)
            for _, r in df.iterrows():
                if r[col] and r[col] != "n/a":
                    img_url = r['blade_image'] if r['blade_image'] else r['beyblade_page_image']
                    img_map[r[col]] = img_url
    
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df, img_map

def get_img(url):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join("images", f"{h}.png")
    if os.path.exists(path): return Image.open(path)
    return None

def add_to_inv(tipo, nome, delta=1):
    if nome and nome != "n/a":
        if nome not in st.session_state.inventario[tipo]:
            st.session_state.inventario[tipo][nome] = 0
        st.session_state.inventario[tipo][nome] += delta
        if st.session_state.inventario[tipo][nome] <= 0:
            if nome in st.session_state.inventario[tipo]:
                del st.session_state.inventario[tipo][nome]

# Inizializzazione
if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}
if 'decks' not in st.session_state:
    st.session_state.decks = [{"name": "IL MIO DECK", "editing": False}]
if 'focus' not in st.session_state:
    st.session_state.focus = {"deck_idx": 0, "slot_idx": None}

df, global_img_map = load_db()

# =========================
# UI PRINCIPALE
# =========================
tab1, tab2, tab3 = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

# --- TAB 1: AGGIUNGI (INTOCCABILE) ---
with tab1:
    st.markdown('<div class="add-container">', unsafe_allow_html=True)
    search_q = st.text_input("Cerca...", "").lower()
    filtered = df[df['_search'].str.contains(search_q)] if search_q else df.head(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container(border=True):
            st.markdown(f"<div class='bey-name'>{row['name']}</div>", unsafe_allow_html=True)
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img: st.image(img, width=150)
            components = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"),
                          ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"),
                          ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            st.write("")
            if st.button("Aggiungi tutto", key=f"all_{i}"):
                for ck, ik in components:
                    if row[ck] and row[ck] != "n/a": add_to_inv(ik, row[ck])
                st.toast("Set aggiunto!")
            st.markdown("<hr style='border-top: 1px solid #475569; margin: 15px 0;'>", unsafe_allow_html=True)
            for ck, ik in components:
                val = row[ck]
                if val and val != "n/a":
                    st.markdown(f"<div class='comp-name-centered'>{val}</div>", unsafe_allow_html=True)
                    if st.button("＋", key=f"btn_{i}_{ck}"):
                        add_to_inv(ik, val)
                        st.toast(f"Aggiunto: {val}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: INVENTARIO ---
with tab2:
    modo = st.radio("Modo", ["Aggiungi (+1)", "Rimuovi (-1)"], horizontal=True, label_visibility="collapsed")
    operazione = 1 if "Aggiungi" in modo else -1
    if not any(st.session_state.inventario.values()):
        st.info("L'inventario è vuoto.")
    else:
        for categoria, pezzi in st.session_state.inventario.items():
            if pezzi:
                with st.expander(categoria.replace('_', ' ').upper(), expanded=False):
                    st.markdown('<div class="inv-row-container">', unsafe_allow_html=True)
                    for nome, qta in pezzi.items():
                        if st.button(f"{nome} x{qta}", key=f"inv_{categoria}_{nome}"):
                            add_to_inv(categoria, nome, operazione)
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: DECK BUILDER ---
with tab3:
    for d_idx, deck in enumerate(st.session_state.decks):
        with st.expander(deck['name'].upper(), expanded=(st.session_state.focus['deck_idx'] == d_idx)):
            
            def get_options(cat, theory=False):
                if theory:
                    csv_map = {"lock_bit": "lock_chip", "blade": "blade", "main_blade": "main_blade",
                               "assist_blade": "assist_blade", "ratchet": "ratchet", "bit": "bit",
                               "ratchet_integrated_bit": "ratchet_integrated_bit"}
                    col_name = csv_map.get(cat, cat)
                    opts = df[col_name].unique().tolist()
                    return ["-"] + sorted([x for x in opts if x and x != "n/a"])
                else:
                    return ["-"] + sorted(list(st.session_state.inventario[cat].keys()))

            tipologie = ["BX/UX", "CX", "BX/UX+RIB", "CX+RIB", "BX/UX Theory", "CX Theory", "BX/UX+RIB Theory", "CX+RIB Theory"]

            for s_idx in range(3):
                # Titolo dinamico
                keys = ["lb", "mb", "ab", "b", "r", "bi", "rib"]
                current_vals = {k: st.session_state.get(f"d{d_idx}_s{s_idx}_{k}", "-") for k in keys}
                parti = [p for p in current_vals.values() if p and p != "-"]
                titolo_slot = " ".join(parti) if parti else f"SLOT {s_idx+1}"
                
                slot_is_open = (st.session_state.focus['deck_idx'] == d_idx and st.session_state.focus['slot_idx'] == s_idx)
                
                with st.expander(titolo_slot.upper(), expanded=slot_is_open):
                    def set_focus(di=d_idx, si=s_idx): st.session_state.focus = {"deck_idx": di, "slot_idx": si}

                    tipo = st.selectbox("Sistema", tipologie, key=f"d{d_idx}_s{s_idx}_type", on_change=set_focus)
                    is_theory = "Theory" in tipo

                    # Form per i menu a tendina
                    if "BX/UX" in tipo and "+RIB" not in tipo:
                        st.selectbox("Blade", get_options("blade", is_theory), key=f"d{d_idx}_s{s_idx}_b", on_change=set_focus)
                        st.selectbox("Ratchet", get_options("ratchet", is_theory), key=f"d{d_idx}_s{s_idx}_r", on_change=set_focus)
                        st.selectbox("Bit", get_options("bit", is_theory), key=f"d{d_idx}_s{s_idx}_bi", on_change=set_focus)
                    elif "CX" in tipo and "+RIB" not in tipo:
                        st.selectbox("Lock Bit", get_options("lock_bit", is_theory), key=f"d{d_idx}_s{s_idx}_lb", on_change=set_focus)
                        st.selectbox("Main Blade", get_options("main_blade", is_theory), key=f"d{d_idx}_s{s_idx}_mb", on_change=set_focus)
                        st.selectbox("Assist Blade", get_options("assist_blade", is_theory), key=f"d{d_idx}_s{s_idx}_ab", on_change=set_focus)
                        st.selectbox("Ratchet", get_options("ratchet", is_theory), key=f"d{d_idx}_s{s_idx}_r", on_change=set_focus)
                        st.selectbox("Bit", get_options("bit", is_theory), key=f"d{d_idx}_s{s_idx}_bi", on_change=set_focus)
                    elif "BX/UX+RIB" in tipo:
                        st.selectbox("Blade", get_options("blade", is_theory), key=f"d{d_idx}_s{s_idx}_b", on_change=set_focus)
                        st.selectbox("RIB", get_options("ratchet_integrated_bit", is_theory), key=f"d{d_idx}_s{s_idx}_rib", on_change=set_focus)
                    elif "CX+RIB" in tipo:
                        st.selectbox("Lock Bit", get_options("lock_bit", is_theory), key=f"d{d_idx}_s{s_idx}_lb", on_change=set_focus)
                        st.selectbox("Main Blade", get_options("main_blade", is_theory), key=f"d{d_idx}_s{s_idx}_mb", on_change=set_focus)
                        st.selectbox("Assist Blade", get_options("assist_blade", is_theory), key=f"ab_{d_idx}_s{s_idx}", on_change=set_focus)
                        st.selectbox("RIB", get_options("ratchet_integrated_bit", is_theory), key=f"d{d_idx}_s{s_idx}_rib", on_change=set_focus)

                    # --- SEZIONE IMMAGINI (AFFIANCATE) ---
                    st.markdown("<br>", unsafe_allow_html=True)
                    # Filtriamo solo i pezzi che hanno un'immagine valida e non sono "-"
                    active_imgs = []
                    for val in current_vals.values():
                        if val != "-":
                            url = global_img_map.get(val)
                            if url: active_imgs.append(url)
                    
                    if active_imgs:
                        cols = st.columns(len(active_imgs))
                        for i, img_url in enumerate(active_imgs):
                            loaded_img = get_img(img_url)
                            if loaded_img:
                                cols[i].image(loaded_img, width=75) # Circa 50% del tab Aggiungi

            # Footer del deck
            st.markdown("<br>", unsafe_allow_html=True)
            if not deck['editing']:
                c1, c2 = st.columns([1, 1])
                if c1.button("📝 Modifica Nome", key=f"edit_btn_{d_idx}"):
                    st.session_state.decks[d_idx]['editing'] = True
                    st.rerun()
                if c2.button("🗑️ Elimina Deck", key=f"del_deck_{d_idx}"):
                    st.session_state.decks.pop(d_idx)
                    st.rerun()
            else:
                new_name = st.text_input("Nuovo nome:", deck['name'], key=f"input_{d_idx}")
                c1, c2 = st.columns([1, 1])
                if c1.button("Salva", key=f"save_{d_idx}"):
                    st.session_state.decks[d_idx]['name'] = new_name
                    st.session_state.decks[d_idx]['editing'] = False
                    st.rerun()
                if c2.button("Annulla", key=f"cancel_{d_idx}"):
                    st.session_state.decks[d_idx]['editing'] = False
                    st.rerun()

    st.write("---")
    if st.button("➕ NUOVO DECK"):
        st.session_state.decks.append({"name": f"NUOVO DECK {len(st.session_state.decks)+1}", "editing": False})
        st.rerun()