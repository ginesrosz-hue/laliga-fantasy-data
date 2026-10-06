import subprocess
import json
import urllib.request
import ssl
import gzip
import sys
import time
from datetime import datetime

OUTPUT_FILE = "mercado_fantasy.json"

def fetch_html():
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    url = "https://www.analiticafantasy.com/mercado"
    
    # 1. Intentar primero con cURL nativo del sistema (el más fiable en GitHub Actions)
    try:
        cmd = ["curl", "-s", "-L", "-A", user_agent, "--compressed", "--max-time", "25", url]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.stdout and "initialPlayers" in res.stdout:
            print("Conectado con éxito mediante cURL nativo")
            return res.stdout
    except Exception as e:
        print(f"Aviso con cURL: {e}")

    # 2. Fallback de seguridad con urllib
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9"
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
        raw_data = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip" or raw_data[:2] == b"\x1f\x8b":
            raw_data = gzip.decompress(raw_data)
        return raw_data.decode("utf-8", errors="ignore")

def fetch_market():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando extracción de LaLiga Fantasy...")
    html = fetch_html()
    
    pos_map = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}
    players = []
    
    idx = html.find("initialPlayers")
    if idx == -1:
        print("❌ Error: No se encontró el bloque de jugadores en la respuesta.")
        sys.exit(1)

    start = html.find("[", idx)
    depth = 0
    end = start
    for i in range(start, len(html)):
        if html[i] == "[":
            depth += 1
        elif html[i] == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    raw_json = html[start:end].replace('\\"', '"').replace('\\\\', '\\')
    try:
        data = json.loads(raw_json)
        for p in data:
            name = p.get("nickname") or p.get("slug", "")
            val = p.get("marketValue", 0)
            change = p.get("subida", 0)
            team = p.get("teamName", "LaLiga")
            pos_id = p.get("positionId", 3)
            photo = p.get("playerPhotoUrl")
            if name and val > 0:
                players.append({
                    "name": name,
                    "market_value": val,
                    "daily_change": change,
                    "position": pos_map.get(pos_id, "MED"),
                    "team": team,
                    "photo_url": photo
                })
    except Exception as e:
        print(f"Error al decodificar JSON: {e}")
        sys.exit(1)

    if not players:
        print("❌ Error: Array de jugadores vacío.")
        sys.exit(1)

    feed_data = {
        "updated_at": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_players": len(players),
        "players": players
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(feed_data, f, ensure_ascii=False, indent=2)

    print(f"✅ ¡Éxito! Se han extraído y guardado {len(players)} futbolistas en {OUTPUT_FILE}.")

if __name__ == "__main__":
    fetch_market()
