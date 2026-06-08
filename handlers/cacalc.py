from telegram import Update
from telegram.ext import ContextTypes
from api.mojang import get_uuid
from api.hypixel import get_profiles
import math

SKILL_XP_TABLE = [
    50, 75, 110, 160, 230, 330, 470, 670, 950, 1340,
    1890, 2665, 3760, 5260, 7380, 10300, 14400, 20000, 27600, 38000,
    52500, 71500, 97000, 132000, 180000, 243000, 328000, 445000, 600000, 800000,
    1065000, 1410000, 1900000, 2500000, 3300000, 4300000, 5600000, 7200000, 9200000, 12000000,
    15000000, 19000000, 24000000, 30000000, 38000000, 48000000, 60000000, 75000000, 93000000, 116250000
]

MAIN_CLASS_XP = 420_000
PASSIVE_CLASS_XP = 105_000
TOTAL_XP_TO_50 = sum(SKILL_XP_TABLE)

def xp_to_level(xp: float) -> float:
    level = 0
    remaining = xp
    for needed in SKILL_XP_TABLE:
        if remaining >= needed:
            remaining -= needed
            level += 1
        else:
            break
    if level >= 50:
        overflow = xp - TOTAL_XP_TO_50
        return 50 + overflow / 200_000_000
    next_xp = SKILL_XP_TABLE[level] if level < len(SKILL_XP_TABLE) else 200_000_000
    return level + remaining / next_xp

def xp_needed_for_target(current_xp: float, target: float) -> float:
    if target <= 50:
        target_xp = TOTAL_XP_TO_50
    else:
        target_xp = TOTAL_XP_TO_50 + (target - 50) * 200_000_000
    return max(0, target_xp - current_xp)

def simulate_runs(class_xp: dict, target: float) -> dict:
    """
    Симулируем раны — каждый ран качаем самый отстающий класс как основной.
    Остальные получают пассивно 105k.
    """
    if target <= 50:
        target_xp = TOTAL_XP_TO_50
    else:
        target_xp = TOTAL_XP_TO_50 + (target - 50) * 200_000_000

    xp = dict(class_xp)
    runs_per_class = {k: 0 for k in xp}
    total_runs = 0

    while any(v < target_xp for v in xp.values()):
        # Находим самый отстающий класс
        main = min(xp, key=lambda k: xp[k])
        if xp[main] >= target_xp:
            break

        # Считаем сколько ранов нужно этому классу как основному
        # пока он не догонит второй по отставанию или не достигнет цели
        others = [k for k in xp if k != main]
        second_worst_xp = min(xp[k] for k in others) if others else target_xp
        needed_to_catch = min(target_xp - xp[main], second_worst_xp - xp[main])

        if needed_to_catch <= 0:
            needed_to_catch = target_xp - xp[main]

        runs = max(1, math.ceil(needed_to_catch / MAIN_CLASS_XP))

        # Применяем раны
        xp[main] += runs * MAIN_CLASS_XP
        xp[main] = min(xp[main], target_xp + MAIN_CLASS_XP)
        runs_per_class[main] += runs
        total_runs += runs

        for k in others:
            xp[k] += runs * PASSIVE_CLASS_XP
            xp[k] = min(xp[k], target_xp + PASSIVE_CLASS_XP)

    return runs_per_class, total_runs

async def cacalc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❗ Укажи ник!\n"
            "Пример: `/cacalc Technoblade` — до CA50\n"
            "Или: `/cacalc Technoblade 55` — до CA55",
            parse_mode="Markdown"
        )
        return

    username = context.args[0]
    target_ca = float(context.args[1]) if len(context.args) > 1 else 50.0

    msg = await update.message.reply_text(f"🔍 Считаю для *{username}*...", parse_mode="Markdown")

    uuid = get_uuid(username)
    if not uuid:
        await msg.edit_text("❌ Игрок не найден.")
        return

    data = get_profiles(uuid)
    if not data:
        await msg.edit_text("❌ Ошибка Hypixel API.")
        return

    profiles = data.get("profiles", [])
    if not profiles:
        await msg.edit_text("❌ Профили не найдены.")
        return

    profile = next((p for p in profiles if p.get("selected")), profiles[0])
    cute_name = profile.get("cute_name", "?")
    member = profile.get("members", {}).get(uuid, {})

    if not member:
        await msg.edit_text("❌ Данные не найдены.")
        return

    dungeons = member.get("dungeons", {})
    player_classes = dungeons.get("player_classes", {})

    class_keys = ["healer", "mage", "berserk", "archer", "tank"]
    class_labels = {
        "healer":  "🌸 Healer",
        "mage":    "🔵 Mage",
        "berserk": "🔴 Berserk",
        "archer":  "🟡 Archer",
        "tank":    "🟢 Tank",
    }

    class_xp = {k: player_classes.get(k, {}).get("experience", 0) for k in class_keys}
    runs_per_class, total_runs = simulate_runs(class_xp, target_ca)

    lines = [f"🧮 *{username}* `[{cute_name}]` → CA *{target_ca:.0f}*\n"]

    for key in class_keys:
        level = xp_to_level(class_xp[key])
        runs = runs_per_class[key]
        label = class_labels[key]
        lines.append(f"{label}: *{level:.2f}* → *{runs:,}* ранов")

    lines.append(f"\n⭐ Всего M7 ранов: *{total_runs:,}*")

    await msg.edit_text("\n".join(lines), parse_mode="Markdown")