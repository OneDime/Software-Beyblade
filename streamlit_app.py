import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image
import streamlit.components.v1 as components

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Officina Beyblade X", layout="wide")

st.markdown("""
<style>
.stApp { background:#0f172a; color:#f1f5f9; }

.card {
    background:#1e293b;
    border:1px solid #334155;
    border-radius:14px;
    padding:14px;
    margin-bottom:14px;
}

.title {
    text-align:center;
    color:#60a5fa;
    margin-bottom:6px;
}

.img-wrap {
    display:flex;
    justify-content:center;
    margin:10px 0;
}
.img-wrap img {
    max-width:180px;
}

.comp {
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin:6px 0;
}

.comp span {
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}

.comp button {
    width:34px;
    height:34px;
    background:#334155;
    color:white;
    border:1px solid #475569;
    border-radius:6px;
}

.full {
    width:100%;
    margin-top:10px;
    padding:10px;
    background:#334155;
    border:1px solid #475569;
    color:white;
    border-radius:8px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# DATA
# =========================
@st.cache_data
def load_db():
    df = pd.read_csv("beyblade_x.csv").fillna("")
    df["_search"] = df.astype(str).apply(lambda x: " ".join(x).lower(), axis=1)
    return df

df = load_db()

if "inventario" not in st.session_state:
    st.session_state.inventario = {
        "lock_bit": {}, "blade": {}, "main_blade": {},
        "assist_blade": {}, "ratchet": {}, "bit": {},
        "ratchet_integrated_bit": {}
    }

# =========================
# TABS
# =========================
tab_add, tab_inv, _ = st.tabs(["🔍 Aggiungi", "📦 Inventario", "🧩 Deck Builder"])

# =========================
# TAB AGGIUNGI (HTML PURO)
# =========================
with tab_add:
    search = st.text_input("Cerca...")
    rows = df[df["_search"].str.contains(search.lower())].head(3) if len(search) >= 2 else df.head(3)

    for idx, row in rows.iterrows():
        html = f"""
        <div class="card">
            <h3 class="title">{row['name'].upper()}</h3>

            <div class="img-wrap">
                <img src="{row['blade_image'] or row['beyblade_page_image']}">
            </div>
        """

        comps = [
            ("lock_chip", "lock_bit"),
            ("blade", "blade"),
            ("main_blade", "main_blade"),
            ("assist_blade", "assist_blade"),
            ("ratchet", "ratchet"),
            ("bit", "bit"),
            ("ratchet_integrated_bit", "ratchet_integrated_bit"),
        ]

        for f, k in comps:
            if row[f] and row[f] != "n/a":
                html += f"""
                <div class="comp">
                    <span>{row[f]}</span>
                    <button onclick="Streamlit.setComponentValue('{k}|{row[f]}')">+</button>
                </div>
                """

        html += """
            <button class="full" onclick="Streamlit.setComponentValue('ALL')">
                Aggiungi tutto
            </button>
        </div>
        """

        res = components.html(html, height=420)

        if res:
            if res == "ALL":
                for f, k in comps:
                    if row[f] and row[f] != "n/a":
                        inv = st.session_state.inventario[k]
                        inv[row[f]] = inv.get(row[f], 0) + 1
            else:
                k, v = res.split("|")
                inv = st.session_state.inventario[k]
                inv[v] = inv.get(v, 0) + 1

# =========================
# TAB INVENTARIO (INVARIATO)
# =========================
with tab_inv:
    for tipo, items in st.session_state.inventario.items():
        if items:
            with st.expander(tipo.replace("_", " ").upper(), True):
                for n, q in items.items():
                    st.write(f"{n} (x{q})")
