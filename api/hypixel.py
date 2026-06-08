import requests
from config import HYPIXEL_KEY

def get_profiles(uuid: str) -> dict | None:
    url = f"https://api.hypixel.net/v2/skyblock/profiles?uuid={uuid}"
    headers = {"API-Key": HYPIXEL_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        if not data.get("success"):
            return None
        return data
    except Exception as e:
        print(f"Ошибка API: {e}")
        return None