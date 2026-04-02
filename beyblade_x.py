import requests
import csv
import time
import re
import os
import hashlib
import sys
from PIL import Image as PILImage
from io import BytesIO

# Forza lo script a lavorare nella cartella dove risiede il file .py
os.chdir(os.path.dirname(os.path.abspath(__file__)))

API_URL = "https://beyblade.fandom.com/api.php"
HEADERS = {
    "User-Agent": "BeybladeX-Infobox-Only/4.3 (contact: local-script)"
}
CSV_FILE = "beyblade_x.csv"

session = requests.Session()
session.headers.update(HEADERS)

# =========================
# API CALL CON RETRY SICURO
# =========================
def api_call(params, label=""):
    attempt = 0
    wait = 1.0
    while True:
        attempt += 1
        try:
            r = session.get(API_URL, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            print(f"    ✘ ERRORE [{label}] {type(e).__name__} - In pausa per {wait}s...")
            time.sleep(wait)
            wait = min(wait * 1.5, 60)
        except ValueError:
            print(f"    ✘ ERRORE [{label}] JSON non valido - In pausa per {wait}s...")
            time.sleep(wait)
            wait = min(wait * 1.5, 60)

# =========================
# FUNZIONI DI SCRAPING
# =========================
def get_beyblade_infobox_pages():
    print("[STEP 1] Recupero pagine con Template:Beyblade Infobox")
    titles = []
    cont = None
    while True:
        params = {
            "action": "query",
            "list": "embeddedin",
            "eititle": "Template:Beyblade Infobox",
            "einamespace": 0,
            "eilimit": 500,
            "format": "json"
        }
        if cont: params["eicontinue"] = cont
        data = api_call(params, "embeddedin")
        if "query" in data and "embeddedin" in data["query"]:
            titles.extend(p["title"] for p in data["query"]["embeddedin"])
        cont = data.get("continue", {}).get("eicontinue")
        if not cont: break
        time.sleep(0.4)
    titles = sorted(set(titles))
    print(f"[OK] Totale pagine candidate: {len(titles)}\n")
    return titles

def get_wikitext(title):
    data = api_call({
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvslots": "main",
        "rvprop": "content",
        "format": "json"
    }, f"wikitext:{title}")
    try:
        pages = data.get("query", {}).get("pages", {})
        if not pages: return ""
        page = next(iter(pages.values()))
        revisions = page.get("revisions", [])
        if not revisions: return ""
        return revisions[0].get("slots", {}).get("main", {}).get("*", "")
    except: return ""

def extract_infobox(wikitext):
    if not wikitext: return {}
    m = re.search(r"\{\{Beyblade Infobox(.*?)\n\}\}", wikitext, re.S | re.I)
    if not m: return {}
    block = m.group(1)
    fields = {}
    current = None
    buf = []
    for line in block.splitlines():
        if line.strip().startswith("|"):
            if current: fields[current] = "\n".join(buf).strip()
            parts = line[1:].split("=", 1)
            current = parts[0].strip()
            buf = [parts[1].strip()] if len(parts) > 1 else []
        else:
            if current: buf.append(line.strip())
    if current: fields[current] = "\n".join(buf).strip()
    return fields

def clean_value(val):
    if not val: return "n/a"
    val = re.sub(r"\{\{.*?\}\}", "", val, flags=re.S)
    val = re.sub(r"\[\[([^|\]]*\|)?([^\]]+)\]\]", r"\2", val)
    val = re.sub(r"<.*?>", "", val)
    return val.strip() if val.strip() else "n/a"

def get_infobox_image(title):
    if title == "n/a": return "n/a"
    try:
        wikitext = get_wikitext(title)
        m = re.search(r"\|\s*image\s*=\s*([^\n|]+)", wikitext, re.I)
        if not m: m = re.search(r"\[\[\s*File\s*:\s*([^\|\]]+)", wikitext, re.I)
        if not m: return "n/a"
        filename = m.group(1).strip()
        data = api_call({
            "action": "query", "titles": f"File:{filename}",
            "prop": "imageinfo", "iiprop": "url", "format": "json"
        }, f"file:{filename}")
        page = next(iter(data.get("query", {}).get("pages", {}).values()))
        info = page.get("imageinfo")
        return info[0]["url"] if info else "n/a"
    except: return "n/a"

def get_pageimage(title):
    if title == "n/a": return "n/a"
    try:
        data = api_call({
            "action": "query", "titles": title, "prop": "pageimages",
            "pithumbsize": 400, "format": "json"
        }, f"pageimg:{title}")
        page = next(iter(data.get("query", {}).get("pages", {}).values()))
        return page.get("thumbnail", {}).get("source", "n/a")
    except: return "n/a"

def resolve_component_page(name, prefixes):
    if name == "n/a": return "n/a"
    for prefix in prefixes:
        title = f"{prefix}{name}"
        try:
            data = api_call({
                "action": "query", "titles": title, "redirects": 1, "format": "json"
            }, f"resolve:{title}")
            page = next(iter(data.get("query", {}).get("pages", {}).values()))
            if int(page.get("pageid", -1)) > 0: return page.get("title", "n/a")
        except: pass
        time.sleep(0.1)
    return "n/a"

def download_and_optimize_images():
    print("\n[STEP] Sincronizzazione immagini...")
    if not os.path.exists("images"): os.makedirs("images")
    image_urls = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                for key in row:
                    if "_image" in key or "page_image" in key:
                        url = row[key]
                        if url and url != "n/a": image_urls.add(url)
    
    print(f"    → Link da verificare: {len(image_urls)}")
    downloaded, skipped = 0, 0
    for url in image_urls:
        filename = hashlib.md5(url.encode()).hexdigest() + ".png"
        filepath = os.path.join("images", filename)
        if os.path.exists(filepath):
            skipped += 1; continue
        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            img = PILImage.open(BytesIO(resp.content))
            if img.mode != 'RGBA': img = img.convert('RGBA')
            target_w = 300
            w_percent = (target_w / float(img.size[0]))
            target_h = int((float(img.size[1]) * float(w_percent)))
            img = img.resize((target_w, target_h), PILImage.Resampling.LANCZOS)
            img.save(filepath, "PNG", optimize=True)
            print(f"    ✔ Salvato: {filename}")
            downloaded += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"    ✘ Errore {url}: {type(e).__name__}")
    print(f"\n[FINE] Sincronizzazione: {downloaded} scaricate, {skipped} già presenti.")

# =========================
# MAIN
# =========================
def create_csv():
    titles = get_beyblade_infobox_pages()
    fields = ["name", "beyblade_page_image", "blade", "blade_image", "main_blade", "main_blade_image",
              "assist_blade", "assist_blade_image", "lock_chip", "lock_chip_image", "ratchet", "ratchet_image",
              "ratchet_integrated_bit", "ratchet_integrated_bit_image", "bit", "bit_image"]

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        kept = 0
        for idx, title in enumerate(titles, 1):
            wikitext = get_wikitext(title)
            m = re.search(r"\|\s*ProductCode\s*=\s*([^\n|]+)", wikitext)
            s = re.search(r"\|\s*System\s*=\s*([^\n|]+)", wikitext)
            p_code = clean_value(m.group(1)) if m else ""
            system_val = clean_value(s.group(1)) if s else ""
            check_text = (p_code + " " + system_val).upper()

            # LOG DI VALUTAZIONE
            if any(k in check_text for k in ["BX", "UX", "CX", "CUSTOM LINE", "BASIC LINE", "UNIQUE LINE"]):
                print(f"[{idx}/{len(titles)}] {title} -> ✅ [KEEP] (X System)")
                info = extract_infobox(wikitext)
                row = {k: "n/a" for k in fields}
                row["name"] = title
                row["beyblade_page_image"] = get_pageimage(title)
                components = {
                    "blade": ["BladeX", "Blade"], "main_blade": ["MainBlade"],
                    "assist_blade": ["AssistBlade"], "lock_chip": ["LockChip", "Lock Bit"],
                    "ratchet": ["Ratchet"], "ratchet_integrated_bit": ["RatchetBit"],
                    "bit": ["Bit", "PerformanceTip"]
                }
                for comp, keys in components.items():
                    for k in keys:
                        val = clean_value(info.get(k))
                        if val != "n/a":
                            row[comp] = val
                            break
                    page = resolve_component_page(row[comp], [f"{comp.replace('_', ' ').title()} - "])
                    img = get_infobox_image(page)
                    if img == "n/a": img = get_pageimage(page)
                    row[f"{comp}_image"] = img
                writer.writerow(row)
                kept += 1
            else:
                print(f"[{idx}/{len(titles)}] {title} -> ❌ [SKIP] (Altro Sistema)")
            
            time.sleep(0.1)
            
        print(f"\n[OK] CSV generato con {kept} Beyblades.")

if __name__ == "__main__":
    print("=== OFFICINA BEYBLADE X - STRUMENTO LOCALE ===")
    print("1 - Crea nuovo CSV (Analisi API completa)")
    print("2 - Scarica/Ottimizza immagini da CSV esistente")
    scelta = input("\nScegli un'opzione (1 o 2): ")

    if scelta == "1":
        create_csv()
        procedi = input("\nVuoi procedere al download delle immagini? (s/n): ")
        if procedi.lower() == 's':
            download_and_optimize_images()
    elif scelta == "2":
        if os.path.exists(CSV_FILE):
            download_and_optimize_images()
        else:
            print(f"Errore: {CSV_FILE} non trovato!")
    
    print("\nLavoro terminato.")
    input("Premi INVIO per chiudere questa finestra...") # Impedisce la chiusura automatica