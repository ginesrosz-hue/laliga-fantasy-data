import json
import urllib.request
import ssl
import subprocess
import sys
from datetime import datetime

OUTPUT_FILE = "mercado_fantasy.json"
API_URL = "https://server.analiticafantasy.com/api/v1/mercado-fantasy/la-liga-fantasy"
FALLBACK_HTML_URL = "https://www.analiticafantasy.com/fantasy-la-liga/mercado"

def fetch_from_api():
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    
    # 1. Intentar con cURL directo a la API JSON del servidor (sin bloqueo de CDN)
    try:
        cmd = [
            "curl", "-s", "-L",
            "-A", user_agent,
            "-H", "Accept: application/json",
            "--compressed", "--max-time", "25",
            API_URL
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.stdout and '"players"' in res.stdout:
            payload = json.loads(res.stdout)
            raw_players = payload.get("data", {}).get("players", [])
            if raw_players:
                print(f"Conectado con éxito a la API JSON directa ({len(raw_players)} registros).")
                return raw_players
    except Exception as e:
        print(f"Aviso en cURL API: {e}")

    # 2. Segundo intento con urllib directo a la API JSON
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(API_URL, headers={
            "User-Agent": user_agent,
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
            raw_players = payload.get("data", {}).get("players", [])
            if raw_players:
                print(f"Conectado por urllib a la API JSON ({len(raw_players)} registros).")
                return raw_players
    except Exception as e:
        print(f"Aviso en urllib API: {e}")

    # 3. Fallback a la nueva ruta HTML con soporte de cookies (-b "")
    try:
        cmd = [
            "curl", "-s", "-L", "-b", "",
            "-A", user_agent,
            "--compressed", "--max-time", "25",
            FALLBACK_HTML_URL
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        html = res.stdout or ""
        idx = html.find("initialPlayers")
        if idx != -1:
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
            return json.loads(raw_json)
    except Exception as e:
        print(f"Aviso en fallback HTML: {e}")

    return []

def fetch_market():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Descargando mercado de LaLiga Fantasy...")
    data = fetch_from_api()

    pos_map = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}
    players = []

    for p in data:
        # Soportar estructura plana o anidada bajo "player"
        item = p.get("player") if isinstance(p.get("player"), dict) else p
        name = item.get("nickname") or item.get("slug", "")
        val = item.get("marketValue", 0)
        change = item.get("subida", 0)
        team = item.get("teamName", "LaLiga")
        pos_id = item.get("positionId", 3)
        master_id = item.get("masterPlayerId")
        photo = item.get("playerPhotoUrl") or (
            f"https://assets.analiticafantasy.com/jugadores/{master_id}.png" if master_id else None
        )
        points = item.get("points", 0)

        if name and val and val > 0:
            players.append({
                "name": name,
                "market_value": val,
                "daily_change": change,
                "position": pos_map.get(pos_id, "MED"),
                "team": team,
                "photo_url": photo,
                "points": points
            })

    if not players:
        print("⚠️ No se pudieron extraer jugadores en esta ejecución.")
        sys.exit(1)

    feed_data = {
        "updated_at": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_players": len(players),
        "players": players
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(feed_data, f, ensure_ascii=False, indent=2)

    print(f"✅ ¡Completado! Se han guardado {len(players)} futbolistas en {OUTPUT_FILE}.")

if __name__ == "__main__":
    fetch_market()
