import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & STILE CSS
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
    <style>
    /* Sfondo generale e font */
    .stApp { background-color: #0f172a; color: #f8fafc; }
    
    /* Card Beyblade: Blu-Grigio scuro, centrata */
    .bey-card {
        background-color: #1e293b; /* Blu-grigio scuro */
        border: 1px solid #334155;
        border-radius: 15px;
        padding: 20px;
        margin: 10px auto;
        max-width: 450px; /* Evita che su desktop diventi troppo larga */
        text-align: center;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }

    /* Intestazione nome beyblade */
    .bey-name-header {
        font-weight: bold;
        font-size: 1.3rem;
        background-color: #3b82f6; /* Blu più vivace per il nome */
        color: white;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 15px;
        text-transform: uppercase;
    }

    /* Riga componenti: Testo e Bottone */
    .comp-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #0f172a;
        margin: 5px 0;
        padding: 8px 12px;
        border-radius: 6px;
    }
    
    .comp-label { font-size: 0.95rem; color: #cbd5e1; }

    /* Bottoni */
    .stButton>button {
        background-color: #334155;
        color: white;
        border: 1px solid #475569;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #3b82f6;
        border-color: #3b82f6;
    }
    
    /* Forza centratura immagini */
    .stImage { display: flex; justify-content: center; }
    
    /* Fix per i flag del deck (li mettiamo su una riga se c'è spazio) */
    .stCheckbox { margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# FUNZIONI CORE
# =========================
@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"): return pd.DataFrame()
    df = pd.read_csv("beyblade_x.csv").fillna("")
    df['_search'] = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    return df

@st.cache_resource
def get_img(url, size=(150, 150)):
    if not url or url == "n/a": return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join("images", f"{h}.png")
    if os.path.exists(path):
        img = Image.open(path)
        img.thumbnail(size)
        return img
    return None

if 'inventario' not in st.session_state:
    st.session_state.inventario = {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]}
if 'decks' not in st.session_state:
    st.session_state.decks = []

df = load_db()
st.sidebar.title("🔧 Officina X")
utente = st.sidebar.selectbox("Utente", ["Antonio", "Andrea", "Fabio"])

# =========================
# TABS
# =========================
tab_add, tab_inv, tab_deck = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

with tab_add:
    search_q = st.text_input("Cerca beyblade o componenti...", key="search_bar")
    
    filtered = df
    if len(search_q) >= 2:
        filtered = df[df['_search'].str.contains(search_q.lower())]
    else:
        filtered = df.head(5)

    for i, (_, row) in enumerate(filtered.iterrows()):
        # Creiamo la card intera con HTML
        st.markdown(f"""
            <div class="bey-card">
                <div class="bey-name-header">{row['name']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # L'immagine e i tasti devono stare dentro il container, 
        # Streamlit non permette di mettere bottoni "dentro" una stringa HTML, 
        # quindi usiamo un trucco di margini negativi o container puliti.
        
        with st.container():
            # Immagine
            img = get_img(row['blade_image'] or row['beyblade_page_image'])
            if img: st.image(img, width=150)
            
            # Lista componenti
            comps = [("lock_chip", "lock_bit"), ("blade", "blade"), ("main_blade", "main_blade"), 
                     ("assist_blade", "assist_blade"), ("ratchet", "ratchet"), ("bit", "bit"), 
                     ("ratchet_integrated_bit", "ratchet_integrated_bit")]
            
            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    c_txt, c_btn = st.columns([0.8, 0.2])
                    c_txt.markdown(f"**{val}**")
                    if c_btn.button("＋", key=f"add_{i}_{field}"):
                        st.session_state.inventario[inv_key][val] = st.session_state.inventario[inv_key].get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            st.button("Aggiungi tutto", key=f"all_{i}", use_container_width=True)

with tab_inv:
    st.header(f"Inventario di {utente}")
    ordine = ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]
    for tipo in ordine:
        pezzi = st.session_state.inventario.get(tipo, {})
        validi = {k: v for k, v in pezzi.items() if v > 0}
        if validi:
            with st.expander(f"{tipo.replace('_', ' ').upper()}", expanded=True):
                for nome, qta in validi.items():
                    c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                    c1.write(f"{nome} (x{qta})")
                    if c2.button("＋", key=f"p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if c3.button("－", key=f"m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()

with tab_deck:
    col_h, col_b = st.columns([2, 1])
    col_h.header(f"Deck di {utente}")
    if col_b.button("➕ Nuovo Deck"):
        st.session_state.decks.append({"name": f"Deck {len(st.session_state.decks)+1}"})

    for d_idx, deck in enumerate(st.session_state.decks):
        with st.expander(f"📂 {deck['name']}", expanded=True):
            for b_idx in range(3):
                st.markdown(f"### Beyblade {b_idx+1}")
                
                f1, f2, f3 = st.columns(3)
                v_cx = f1.checkbox("CX", key=f"cx_{d_idx}_{b_idx}")
                v_rib = f2.checkbox("RIB", key=f"rib_{d_idx}_{b_idx}")
                v_th = f3.checkbox("Theory", key=f"th_{d_idx}_{b_idx}")
                
                rows = []
                if v_cx: rows += [("Lock Bit", "lock_chip", "lock_chip_image"), ("Main Blade", "main_blade", "main_blade_image"), ("Assist Blade", "assist_blade", "assist_blade_image")]
                else: rows += [("Blade", "blade", "blade_image")]
                if v_rib: rows += [("R.I.B.", "ratchet_integrated_bit", "ratchet_integrated_bit_image")]
                else: rows += [("Ratchet", "ratchet", "ratchet_image"), ("Bit", "bit", "bit_image")]

                for label, db_key, img_db_key in rows:
                    if v_th: opts = [""] + sorted(df[db_key].unique().tolist())
                    else:
                        inv_k = "lock_bit" if db_key == "lock_chip" else db_key
                        opts = [""] + sorted(list(st.session_state.inventario.get(inv_k, {}).keys()))
                    
                    # Layout orizzontale per smartphone: Menu a sinistra, immagine a destra
                    cd1, cd2 = st.columns([0.7, 0.3])
                    scelta = cd1.selectbox(label, opts, key=f"s_{d_idx}_{b_idx}_{db_key}")
                    if scelta:
                        img_url = df[df[db_key] == scelta][img_db_key].values
                        if len(img_url) > 0:
                            p_img = get_img(img_url[0], size=(80, 80))
                            if p_img: cd2.image(p_img)