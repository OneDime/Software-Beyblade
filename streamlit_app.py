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
.stApp {
    background-color: #0f172a;
    color: #f1f5f9;
}

/* CARD */
div[data-testid="stContainer"] {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 16px;
}

/* CENTRATURA GLOBALE */
.center {
    text-align: center;
}

/* IMMAGINE */
.center img {
    margin-left: auto;
    margin-right: auto;
    display: block;
}

/* BOTTONI */
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
# TAB AGGIUNGI — CENTRATURA REALE
# =========================
with tab_add:
    search_q = st.text_input("Cerca...", key="search_main")
    filtered = df[df["_search"].str.contains(search_q.lower())].head(3) if len(search_q) >= 2 else df.head(3)

    for i, (_, row) in enumerate(filtered.iterrows()):
        with st.container():

            # ---- TITOLO ----
            st.markdown(
                f"<div class='center'><h3 style='color:#60a5fa'>{row['name'].upper()}</h3></div>",
                unsafe_allow_html=True
            )

            # ---- IMMAGINE ----
            img = get_img(row["blade_image"] or row["beyblade_page_image"])
            if img:
                st.markdown("<div class='center'>", unsafe_allow_html=True)
                st.image(img)
                st.markdown("</div>", unsafe_allow_html=True)

            st.divider()

            # ---- COMPONENTI (CENTRATE) ----
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
                    st.markdown(
                        f"<div class='center'><strong>{val}</strong></div>",
                        unsafe_allow_html=True
                    )
                    if st.button(f"＋ Aggiungi {val}", key=f"add_{i}_{field}", use_container_width=True):
                        inv = st.session_state.inventario[inv_key]
                        inv[val] = inv.get(val, 0) + 1
                        st.toast(f"Aggiunto {val}")

            # ---- AGGIUNGI TUTTO ----
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
