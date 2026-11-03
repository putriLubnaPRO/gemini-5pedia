import sqlite3
import urllib.request
import urllib.parse
import json
import ssl
import re

DB_FILE = "ultimate_5pedia_warehouse.db"

def init_warehouses():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Tabel chat sekarang memiliki kolom 'email' untuk memisahkan data tiap akun
    cursor.execute('''CREATE TABLE IF NOT EXISTS gudang_chat (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, role TEXT, content TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS gudang_fakta (id INTEGER PRIMARY KEY AUTOINCREMENT, keyword TEXT UNIQUE, info TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS gudang_pedia (id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT, source TEXT, result TEXT)''')
    
    fakta_awal = [
        ("lokomotif", "Lokomotif adalah sarana penggerak kereta api yang memiliki motor atau mesin sendiri."),
        ("ai", "Artificial Intelligence adalah sistem komputer yang dirancang untuk berpikir dan merespons layaknya manusia."),
        ("python", "Python adalah bahasa pemrograman tingkat tinggi yang fleksibel dan mudah dipelajari."),
        ("scp 173", "SCP-173 adalah objek fiktif dari SCP Foundation berupa patung beton yang tidak dapat bergerak jika sedang ditatap langsung.")
    ]
    cursor.executemany("INSERT OR IGNORE INTO gudang_fakta (keyword, info) VALUES (?, ?)", fakta_awal)
    conn.commit()
    conn.close()

def simpan_gudang_chat(email, role, content):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO gudang_chat (email, role, content) VALUES (?, ?, ?)", (email, role, content))
    conn.commit()
    conn.close()

def ambil_riwayat_chat(email, limit=20):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM gudang_chat WHERE email = ? ORDER BY id DESC LIMIT ?", (email, limit))
    rows = cursor.fetchall()
    conn.close()
    return list(reversed(rows))

def cari_gudang_fakta(query):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT info FROM gudang_fakta WHERE keyword = ?", (query,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else ""

def ambil_dari_cache_pedia(query, source):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT result FROM gudang_pedia WHERE query = ? AND source = ?", (query, source))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def simpan_ke_cache_pedia(query, source, result):
    if not result: return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO gudang_pedia (query, source, result) VALUES (?, ?, ?)", (query, source, result))
    conn.commit()
    conn.close()

def fetch_direct_youtube(url):
    cached = ambil_dari_cache_pedia(url, "direct_youtube")
    if cached is not None: return cached
    try:
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=6) as res:
            html = res.read().decode("utf-8")
            title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', html)
            title = title_match.group(1) if title_match else "Video YouTube"
            desc = desc_match.group(1) if desc_match else "Tidak ada deskripsi."
            res_text = f"• **Judul:** {title}\n• **Deskripsi:** {desc[:250]}...\n🔗 *{url}*"
            simpan_ke_cache_pedia(url, "direct_youtube", res_text)
            return res_text
    except Exception as e:
        return f"Gagal membaca YouTube: {e}"

def fetch_wikipedia(query):
    cached = ambil_dari_cache_pedia(query, "wikipedia")
    if cached is not None: return cached
    try:
        ctx = ssl._create_unverified_context()
        url = f"https://id.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote_plus(query)}&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=4) as res:
            data = json.loads(res.read().decode("utf-8"))
            results = data.get("query", {}).get("search", [])
            if not results: return ""
            title = results[0]["title"]
        detail_url = f"https://id.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={urllib.parse.quote_plus(title)}&format=json"
        req_det = urllib.request.Request(detail_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_det, context=ctx, timeout=4) as res_det:
            det_data = json.loads(res_det.read().decode("utf-8"))
            for pid, pinfo in det_data.get("query", {}).get("pages", {}).items():
                if "extract" in pinfo:
                    res_text = pinfo["extract"]
                    simpan_ke_cache_pedia(query, "wikipedia", res_text)
                    return res_text
    except:
        pass
    return ""

def fetch_wikisource(query):
    cached = ambil_dari_cache_pedia(query, "wikisource")
    if cached is not None: return cached
    try:
        ctx = ssl._create_unverified_context()
        url = f"https://id.wikisource.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote_plus(query)}&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=4) as res:
            data = json.loads(res.read().decode("utf-8"))
            results = data.get("query", {}).get("search", [])
            if not results: return ""
            title = results[0]["title"]
        detail_url = f"https://id.wikisource.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={urllib.parse.quote_plus(title)}&format=json"
        req_det = urllib.request.Request(detail_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_det, context=ctx, timeout=4) as res_det:
            det_data = json.loads(res_det.read().decode("utf-8"))
            for pid, pinfo in det_data.get("query", {}).get("pages", {}).items():
                if "extract" in pinfo:
                    res_text = pinfo["extract"]
                    simpan_ke_cache_pedia(query, "wikisource", res_text)
                    return res_text
    except:
        pass
    return ""

def fetch_wikivoyage(query):
    cached = ambil_dari_cache_pedia(query, "wikivoyage")
    if cached is not None: return cached
    try:
        ctx = ssl._create_unverified_context()
        url = f"https://id.wikivoyage.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote_plus(query)}&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=4) as res:
            data = json.loads(res.read().decode("utf-8"))
            results = data.get("query", {}).get("search", [])
            if not results: return ""
            title = results[0]["title"]
        detail_url = f"https://id.wikivoyage.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={urllib.parse.quote_plus(title)}&format=json"
        req_det = urllib.request.Request(detail_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_det, context=ctx, timeout=4) as res_det:
            det_data = json.loads(res_det.read().decode("utf-8"))
            for pid, pinfo in det_data.get("query", {}).get("pages", {}).items():
                if "extract" in pinfo:
                    res_text = pinfo["extract"]
                    simpan_ke_cache_pedia(query, "wikivoyage", res_text)
                    return res_text
    except:
        pass
    return ""

def generate_ai_brain_response(user_input):
    text_lower = user_input.lower()
    if any(kw in text_lower for kw in ["html", "web", "website"]):
        return "🤖 **AI Code Generator (HTML):**\n```html\n<!DOCTYPE html>\n<html>\n<head><title>Web</title></head>\n<body><h1>Halo Dunia</h1></body>\n</html>\n```"
    elif any(kw in text_lower for kw in ["python", "py"]):
        return "🤖 **AI Code Generator (Python):**\n```python\nprint('Halo dari 5Pedia AI!')\n```"
    else:
        return f"🤖 **AI Brain Assistant:**\n\nTopik mengenai **'{user_input}'** telah dianalisis. Saya siap membantu memberikan penjelasan terperinci atau membuatkan kode program sesuai kebutuhanmu!"

def proses_gabungan_multipedia(user_input):
    text_lower = user_input.strip().lower()
    if "youtube.com" in text_lower or "youtu.be" in text_lower:
        words = user_input.split()
        yt_url = next((w for w in words if "youtube.com" in w or "youtu.be" in w), "")
        if yt_url:
            return f"📺 **Analisis YouTube:**\n{fetch_direct_youtube(yt_url)}"
    
    query_bersih = re.sub(r'[^\w\s]', '', text_lower).strip()
    data_wiki = fetch_wikipedia(query_bersih)
    data_source = fetch_wikisource(query_bersih)
    data_voyage = fetch_wikivoyage(query_bersih)

    sections = []
    if data_wiki: sections.append(f"📖 **Wikipedia:**\n{data_wiki}")
    if data_source: sections.append(f"📜 **Wikisource:**\n{data_source}")
    if data_voyage: sections.append(f"🧭 **Wikivoyage:**\n{data_voyage}")

    if sections:
        return "✨ **Hasil Penelusuran Pedia:**\n\n" + "\n\n".join(sections)
    return generate_ai_brain_response(user_input)
  
