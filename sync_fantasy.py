import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

OUTPUT_FILE = "mercado_fantasy.json"

# Cabecera para navegar como un usuario estándar
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9"
}

def clean_number(text):
    """Convierte texto de precio como '14.500.000 €' o '+250.000' en un número entero limpio"""
    if not text:
        return 0
    clean = re.sub(r"[^\d\-+]", "", text.replace(".", "").replace(",", ""))
    try:
        return int(clean)
    except ValueError:
        return 0

def fetch_market():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando extracción diaria de LaLiga Fantasy...")
    players = []

    # Fuentes web públicas que recogen el mercado matinal de LaLiga Fantasy
    sources = [
        "https://www.analiticafantasy.com/mercado/la-liga-fantasy",
        "https://www.comuniazo.com/la-liga-fantasy/mercado"
    ]

    for source_url in sources:
        try:
            print(f"Consultando fuente: {source_url}")
            resp = requests.get(source_url, headers=HEADERS, timeout=20)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                rows = soup.select("table tr, div.player-row, div.market-item")

                for row in rows:
                    cols = row.find_all(["td", "div"])
                    if len(cols) >= 3:
                        texts = [c.get_text(strip=True) for c in cols if c.get_text(strip=True)]
                        if len(texts) >= 3:
                            name = texts[0]
                            # Saltar filas de encabezado de tabla
                            if name.lower() in ["jugador", "nombre", "player", "futbolista"]:
                                continue
                            
                            val = clean_number(texts[1])
                            change = clean_number(texts[2])
                            
                            if val > 0:
                                players.append({
                                    "name": name,
                                    "market_value": val,
                                    "daily_change": change,
                                    "position": "MED",
                                    "team": texts[3] if len(texts) > 3 else "LaLiga"
                                })

                if len(players) > 10:
                    print(f"¡Éxito! Se han extraído {len(players)} jugadores de {source_url}.")
                    break
        except Exception as e:
            print(f"Aviso al consultar {source_url}: {e}")

    # Estructura del archivo JSON que descargará la app móvil
    feed_data = {
        "updated_at": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_players": len(players),
        "players": players
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(feed_data, f, ensure_ascii=False, indent=2)

    print(f"Archivo '{OUTPUT_FILE}' guardado con éxito.")

if __name__ == "__main__":
    fetch_market()
