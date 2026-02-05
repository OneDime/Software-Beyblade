import csv, io, hashlib, requests
from PIL import Image
import streamlit as st

# =========================
# CONFIG
# =========================
IMG_SIZE = (80, 80)
inventario = {
    "lock_bit": {}, "blade": {}, "main_blade": {}, "assist_blade": {},
    "ratchet": {}, "ratchet_integrated_bit": {}, "bit": {}
}

st.set_page_config(page_title="🔧 Officina Beyblade X", layout="wide")

# =========================
# UTILS
# =========================
def clean(v):
    if not v or str(v).lower() == "n/a":
        return ""
    return str(v).strip()

def pretty(v):
    return v.replace(" (", "\n(")

def load_image(url):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content))
        img.thumbnail(IMG_SIZE, Image.Resampling.LANCZOS)
        return img
    except:
        return None

# =========================
# CARICAMENTO CSV
# =========================
uploaded_file = st.file_uploader("Carica CSV database", type=["csv"])
beyblades = []

if uploaded_file:
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
        search = " ".join(bey[k] for k in ["nome","blade","main_blade","assist_blade","lock_bit","ratchet","ratchet_integrated_bit","bit"] if bey[k])
        bey["_search"] = " ".join(search.casefold().split())
        beyblades.append(bey)

# =========================
# SEARCH
# =========================
search_query = st.text_input("Cerca:")
if search_query:
    q = search_query.casefold().strip()
    filtered_beyblades = [b for b in beyblades if q in b["_search"]]
else:
    filtered_beyblades = beyblades

# =========================
# TAB SIMULATI (Aggiungi / Inventario)
# =========================
st.header("➕ Aggiungi")
for bey in filtered_beyblades:
    st.subheader(pretty(bey["nome"]))
    img_url = bey["blade_img"] or bey["beyblade_page_image"] or bey["main_blade_img"] or bey["lock_bit_img"]
    if img_url:
        img = load_image(img_url)
        if img:
            st.image(img, use_column_width=True)
    for k in ["lock_bit","blade","main_blade","assist_blade","ratchet","ratchet_integrated_bit","bit"]:
        if bey[k]:
            if st.button(f"+ {k}: {pretty(bey[k])}", key=f"{bey['nome']}_{k}"):
                inventario[k][bey[k]] = inventario[k].get(bey[k], 0) + 1
    if st.button("Aggiungi tutto", key=f"{bey['nome']}_all"):
        for k in inventario:
            if bey.get(k):
                inventario[k][bey[k]] = inventario[k].get(bey[k],0)+1

st.header("📦 Inventario")
for tipo, items in inventario.items():
    st.subheader(tipo.replace("_"," ").title())
    for nome, count in items.items():
        col1, col2 = st.columns([3,1])
        col1.write(f"{nome} ×{count}")
        if col2.button("-", key=f"rm_{tipo}_{nome}"):
            inventario[tipo][nome]-=1
            if inventario[tipo][nome]<=0:
                del inventario[tipo][nome]
