import json
import urllib.request
from datetime import datetime

OUTPUT_FILE = "mercado_fantasy.json"

def fetch_market():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Conectando con los datos de LaLiga Fantasy...")
    
    url = "https://www.analiticafantasy.com/mercado"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9"
    }
    
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    # Mapeo de IDs de posición oficial
    pos_map = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}

    # Extraer el array de jugadores
    players = []
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
            print(f"Error al decodificar: {e}")

    feed_data = {
        "updated_at": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_players": len(players),
        "players": players
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(feed_data, f, ensure_ascii=False, indent=2)

    print(f"✅ ¡Completado con éxito! Se han extraído {len(players)} futbolistas.")

if __name__ == "__main__":
    fetch_market()
