import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image

# =========================
# CONFIGURAZIONE & CSS
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0f172a; color: #f1f5f9; }

/* CARD */
[data-testid="stContainer"] {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 14px;
}

/* NOME CENTRATO */
.bey-title {
    text-align: center;
    color: #60a5fa;
    margin-bottom: 6px;
}

/* IMMAGINE CENTRATA */
.bey-img {
    display: flex;
    justify-content: center;
    margin: 8px 0 12px 0;
}
.bey-img img {
    max-width: 180px;
}

/* RIGA COMPONENTE */
.comp-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin: 6px 0;
}

.comp-name {
    flex: 1;
    text-align: left;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* BOTTONE + PICCOLO */
.comp-btn button {
    width: 38px !important;
    min-width: 38px !important;
    padding: 0 !important;
}

/* BOTTONI GENERALI */
.stButton button {
    background-color: #334155 !important;
    color: #f1f5f9 !important;
    border: 1px solid #475569 !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# FUNZIONI
# =========================
@st.cache_data
def load_db():
    if not os.path.exists("beyblade_x.csv"):
        return pd.DataFrame()
    df = pd.read_csv("beyblade_x.csv").fillna("")
    df["_search"] = df.astype(str).apply(lambda x: " ".join(x).lower(), axis=1)
    return df

@st.cache_resource
def get_img(url, size=(180, 180)):
    if not url or url == "n/a":
        return None
    h = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join("images", f"{h}.png")
    if os.path.exists(path):
        img = Image.open(path)
        img.thumbnail(size)
        return img
    return None

# =========================
# DATA
# =========================
df = load_db()

if "inventario" not in st.session_state:
    st.session_state.inventario = {
        "lock_bit": {},
        "blade": {},
        "main_blade": {},
        "assist_blade": {},
        "ratchet": {},
        "bit": {},
        "ratchet_integrated_bit": {}
    }

# =========================
# UI
# =========================
tab_add, tab_inv, tab_deck = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

# =========================
# TAB AGGIUNGI (MOBILE FIX DEFINITIVO)
# =========================
with tab_add:
    search_q = st.text_input("Cerca...", key="search_main")
    filtered = df[df["_search"].str.contains(search_q.lower())].head(3) if len(search_q) >= 2 else df.head(3)

    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container():

            # NOME
            st.markdown(
                f"<h3 class='bey-title'>{row['name'].upper()}</h3>",
                unsafe_allow_html=True
            )

            # IMMAGINE
            img = get_img(row["blade_image"] or row["beyblade_page_image"])
            if img:
                st.markdown("<div class='bey-img'>", unsafe_allow_html=True)
                st.image(img)
                st.markdown("</div>", unsafe_allow_html=True)

            st.divider()

            # COMPONENTI
            comps = [
                ("lock_chip", "lock_bit"),
                ("blade", "blade"),
                ("main_blade", "main_blade"),
                ("assist_blade", "assist_blade"),
                ("ratchet", "ratchet"),
                ("bit", "bit"),
                ("ratchet_integrated_bit", "ratchet_integrated_bit")
            ]

            for field, inv_key in comps:
                val = row[field]
                if val and val != "n/a":
                    col_text, col_btn = st.columns([0.85, 0.15])
                    with col_text:
                        st.markdown(
                            f"<div class='comp-row'><div class='comp-name'>{val}</div></div>",
                            unsafe_allow_html=True
                        )
                    with col_btn:
                        st.markdown("<div class='comp-btn'>", unsafe_allow_html=True)
                        if st.button("＋", key=f"add_{i}_{field}"):
                            inv = st.session_state.inventario[inv_key]
                            inv[val] = inv.get(val, 0) + 1
                            st.toast(f"Aggiunto {val}")
                        st.markdown("</div>", unsafe_allow_html=True)

            # AGGIUNGI TUTTO (UNICO FULL WIDTH)
            if st.button("Aggiungi tutto", key=f"all_{i}", use_container_width=True):
                for f, k in comps:
                    if row[f] and row[f] != "n/a":
                        inv = st.session_state.inventario[k]
                        inv[row[f]] = inv.get(row[f], 0) + 1
                st.toast("Set aggiunto")

# =========================
# TAB INVENTARIO (INVARIATO)
# =========================
with tab_inv:
    st.header("Inventario")
    for tipo in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]:
        pezzi = st.session_state.inventario.get(tipo, {})
        validi = {k: v for k, v in pezzi.items() if v > 0}
        if validi:
            with st.expander(tipo.replace("_", " ").upper(), expanded=True):
                for nome, qta in validi.items():
                    ci1, ci2, ci3 = st.columns([0.6, 0.2, 0.2])
                    ci1.write(f"{nome} (x{qta})")
                    if ci2.button("＋", key=f"inv_p_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] += 1
                        st.rerun()
                    if ci3.button("－", key=f"inv_m_{tipo}_{nome}"):
                        st.session_state.inventario[tipo][nome] -= 1
                        st.rerun()
