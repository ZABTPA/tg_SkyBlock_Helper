import requests
from config import HYPIXEL_KEY

SKILL_XP_TABLE = [
    50, 125, 200, 300, 500, 750, 1000, 1500, 2000, 3500,
    5000, 7500, 10000, 15000, 20000, 30000, 50000, 75000, 100000, 200000,
    300000, 400000, 500000, 600000, 700000, 800000, 900000, 1000000, 1100000, 1200000,
    1300000, 1400000, 1500000, 1600000, 1700000, 1800000, 1900000, 2000000, 2100000, 2200000,
    2300000, 2400000, 2500000, 2600000, 2750000, 2900000, 3100000, 3400000, 3700000, 4000000,
    4300000, 4600000, 4900000, 5200000, 5500000, 5800000, 6100000, 6400000, 6700000, 7000000
]

def xp_to_level(xp: float) -> int:
    level = 0
    for needed in SKILL_XP_TABLE:
        if xp >= needed:
            xp -= needed
            level += 1
        else:
            break
    return level

def get_profiles(uuid: str) -> dict | None:
    url = f"https://api.hypixel.net/v2/skyblock/profiles?uuid={uuid}"
    headers = {"API-Key": HYPIXEL_KEY}
    r = requests.get(url, headers=headers)
    data = r.json()
    print(data)  # добавили эту строку
    if not data.get("success"):
        return None
    return data

def get_best_profile(data: dict, uuid: str) -> dict | None:
    profiles = data.get("profiles", [])
    if not profiles:
        return None
    best = max(
        profiles,
        key=lambda p: sum(
            p.get("members", {}).get(uuid, {}).get(f"experience_skill_{s}", 0)
            for s in ["combat", "mining", "farming", "fishing", "foraging", "enchanting", "alchemy", "taming"]
        )
    )
    return best.get("members", {}).get(uuid, {})

def parse_skills(member: dict) -> dict:
    skill_names = {
        "SKILL_COMBAT":     "⚔️ Combat",
        "SKILL_MINING":     "⛏️ Mining",
        "SKILL_FARMING":    "🌾 Farming",
        "SKILL_FISHING":    "🎣 Fishing",
        "SKILL_FORAGING":   "🪓 Foraging",
        "SKILL_ENCHANTING": "🏹 Enchanting",
        "SKILL_ALCHEMY":    "🧪 Alchemy",
        "SKILL_TAMING":     "❤️ Taming",
    }
    experience = member.get("player_data", {}).get("experience", {})
    result = {}
    for key, label in skill_names.items():
        xp = experience.get(key, 0)
        result[label] = {"xp": xp, "level": xp_to_level(xp)}
    return result