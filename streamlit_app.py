import csv
import io
import json
import hashlib
import requests
from PIL import Image
import streamlit as st
from io import BytesIO

# =========================
# CONFIG
# =========================
CSV_FILE = "beyblade_x.csv"
IMG_SIZE = (80, 80)

# =========================
# UTILS
# =========================
@st.cache_data(show_spinner=False)
def clean(v):
    if not v or str(v).lower() == "n/a":
        return ""
    return str(v).strip()

@st.cache_data(show_spinner=False)
def pretty(v):
    return v.replace(" (", "\n(")

@st.cache_data(show_spinner=False)
def image_path(url):
    h = hashlib.md5(url.encode()).hexdigest()
    return h  # usiamo l'hash come chiave cache

@st.cache_resource(show_spinner=False)
def load_image(url):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=8, allow_redirects=True)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content))
        img.thumbnail(IMG_SIZE, Image.Resampling.LANCZOS)
        return img
    except Exception:
        return None

# =========================
# DATABASE
# =========================
@st.cache_data(show_spinner=False)
def load_database():
    beyblades = []
    if not st.secrets.get("CSV_CONTENT") and not st.file_uploader("Carica CSV database"):
        return beyblades
    try:
        if st.secrets.get("CSV_CONTENT"):
            f = io.StringIO(st.secrets["CSV_CONTENT"])
        else:
            uploaded_file = st.file_uploader("Carica CSV database", type=["csv"])
            if not uploaded_file:
                return beyblades
            f = io.StringIO(uploaded_file.getvalue().decode("utf-8"))

        reader = csv.DictReader(f)
        for r in reader:
            bey = {
                "nome": clean(r.get("name")),
                "blade": clean(r.get("blade")),
                "main_blade": clean(r.get("main_blade")),
                "assist_blade": clean(r.get("assist_blade")),
                "lock_bit": clean(r.get("lock_chip")),
                "ratchet": clean(r.get("ratchet")),
                "ratchet_integrated_bit": clean(r.get("ratchet_integrated_bit")),
                "bit": clean(r.get("bit")),
                "beyblade_page_image": clean(r.get("beyblade_page_image")),
                "blade_img": clean(r.get("blade_image")),
                "main_blade_img": clean(r.get("main_blade_image")),
                "assist_blade_img": clean(r.get("assist_blade_image")),
                "lock_bit_img": clean(r.get("lock_chip_image")),
                "ratchet_img": clean(r.get("ratchet_image")),
                "ratchet_integrated_bit_img": clean(r.get("ratchet_integrated_bit_image")),
                "bit_img": clean(r.get("bit_image")),
            }
            search = " ".join(bey[k] for k in ["nome", "blade", "main_blade", "assist_blade", "lock_bit", "ratchet", "ratchet_integrated_bit", "bit"] if bey[k])
            bey["_search"] = " ".join(search.casefold().split())
            beyblades.append(bey)
    except Exception:
        pass
    return beyblades

# =========================
# INVENTORY (in RAM per ora)
# =========================
inventario = {
    "lock_bit": {}, "blade": {}, "main_blade": {}, "assist_blade": {},
    "ratchet": {}, "ratchet_integrated_bit": {}, "bit": {}
}

# =========================
# STREAMLIT APP
# =========================
st.set_page_config(page_title="🔧 Officina Beyblade X – Stabile", layout="wide")

beyblades = load_database()
filtered_beyblades = list(beyblades)

tabs = st.tabs(["➕ Aggiungi", "📦 Inventario", "🧩 Deck"])
tab_add, tab_inv, tab_deck = tabs

# =========================
# TAB AGGIUNGI
# =========================
with tab_add:
    search_query = st.text_input("Cerca:")
    if search_query:
        q = search_query.casefold().strip()
        filtered_beyblades = [b for b in beyblades if q in b["_search"]]

    cols_per_row = 3
    for i in range(0, len(filtered_beyblades), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, bey in enumerate(filtered_beyblades[i:i+cols_per_row]):
            col = cols[j]
            col.markdown(f"**{pretty(bey['nome'])}**")
            img_url = bey["blade_img"] or bey["beyblade_page_image"] or bey["main_blade_img"] or bey["lock_bit_img"]
            if img_url:
                img = load_image(img_url)
                if img:
                    col.image(img, use_column_width=True)

            order = [("lock_bit", "Lock Bit"), ("blade", "Blade"), ("main_blade", "Main Blade"), ("assist_blade", "Assist Blade"),
                     ("ratchet", "Ratchet"), ("ratchet_integrated_bit", "R.I.B."), ("bit", "Bit")]
            for k, label in order:
                if bey[k]:
                    if col.button(f"+ {label}: {pretty(bey[k])}", key=f"{bey['nome']}_{k}"):
                        inventario[k][bey[k]] = inventario[k].get(bey[k], 0) + 1
            if col.button("Aggiungi tutto", key=f"{bey['nome']}_all"):
                for k in inventario:
                    if bey.get(k):
                        inventario[k][bey[k]] = inventario[k].get(bey[k], 0) + 1

# =========================
# TAB INVENTARIO
# =========================
with tab_inv:
    for tipo in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "ratchet_integrated_bit", "bit"]:
        st.subheader(tipo.replace("_", " ").title())
        items = inventario[tipo]
        for nome, count in items.items():
            col1, col2 = st.columns([3,1])
            col1.write(f"{nome} ×{count}")
            if col2.button("-", key=f"rm_{tipo}_{nome}"):
                inventario[tipo][nome] -= 1
                if inventario[tipo][nome] <= 0:
                    del inventario[tipo][nome]

# =========================
# TAB DECK
# =========================
# Decks in RAM
if "decks" not in st.session_state:
    st.session_state.decks = [{"name": f"Deck 1", "beys": [{"parts": {}, "flags": {"cx": False, "rib": False, "theory": False}} for _ in range(3)]}]

def get_unique_from_db(key):
    return sorted(list(set(b[key] for b in beyblades if b[key])))

def update_deck_part(deck_idx, bey_idx, key, val):
    st.session_state.decks[deck_idx]["beys"][bey_idx]["parts"][key] = val

with tab_deck:
    if st.button("➕ Crea Nuovo Deck"):
        st.session_state.decks.append({"name": f"Deck {len(st.session_state.decks)+1}",
                                       "beys": [{"parts": {}, "flags": {"cx": False, "rib": False, "theory": False}} for _ in range(3)]})
    for d_idx, deck in enumerate(st.session_state.decks):
        st.markdown(f"### 📂 {deck['name']}")
        cols = st.columns(3)
        for b_idx, bey_data in enumerate(deck["beys"]):
            with cols[b_idx]:
                st.markdown(f"**Beyblade {b_idx+1}**")
                flags = bey_data["flags"]
                cx = st.checkbox("CX", value=flags["cx"], key=f"cx_{d_idx}_{b_idx}")
                rib = st.checkbox("RIB", value=flags["rib"], key=f"rib_{d_idx}_{b_idx}")
                theory = st.checkbox("Theory", value=flags["theory"], key=f"th_{d_idx}_{b_idx}")
                bey_data["flags"].update({"cx": cx, "rib": rib, "theory": theory})

                rows = []
                if cx:
                    rows += [("lock_bit", "Lock Bit", "lock_bit_img"), ("main_blade", "Main Blade", "main_blade_img"), ("assist_blade", "Assist Blade", "assist_blade_img")]
                else:
                    rows += [("blade", "Blade", "blade_img")]
                if rib:
                    rows += [("ratchet_integrated_bit", "R.I.B.", "ratchet_integrated_bit_img")]
                else:
                    rows += [("ratchet", "Ratchet", "ratchet_img"), ("bit", "Bit", "bit_img")]

                for key, lbl, img_k in rows:
                    options = get_unique_from_db(key) if theory else sorted(list(inventario[key].keys()))
                    val = bey_data["parts"].get(key, "")
                    sel = st.selectbox(lbl, options=options, index=options.index(val) if val in options else 0, key=f"{d_idx}_{b_idx}_{key}")
                    update_deck_part(d_idx, b_idx, key, sel)
                    # immagine
                    img_url = next((b[img_k] or b["beyblade_page_image"] for b in beyblades if b[key]==sel), None)
                    if img_url:
                        img = load_image(img_url)
                        if img:
                            st.image(img, use_column_width=True)
        if st.button("🗑️ Elimina Deck", key=f"rmdeck_{d_idx}"):
            st.session_state.decks.pop(d_idx)
            st.experimental_rerun()
