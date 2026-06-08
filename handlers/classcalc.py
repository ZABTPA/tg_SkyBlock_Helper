from telegram import Update
from telegram.ext import ContextTypes
from api.mojang import get_uuid
from api.hypixel import get_profiles

SKILL_XP_TABLE = [
    50, 75, 110, 160, 230, 330, 470, 670, 950, 1340,
    1890, 2665, 3760, 5260, 7380, 10300, 14400, 20000, 27600, 38000,
    52500, 71500, 97000, 132000, 180000, 243000, 328000, 445000, 600000, 800000,
    1065000, 1410000, 1900000, 2500000, 3300000, 4300000, 5600000, 7200000, 9200000, 12000000,
    15000000, 19000000, 24000000, 30000000, 38000000, 48000000, 60000000, 75000000, 93000000, 116250000
]

MAIN_CLASS_XP = 420_000
TOTAL_XP_TO_50 = sum(SKILL_XP_TABLE)

CLASS_ALIASES = {
    "healer": "healer", "heal": "healer", "h": "healer",
    "mage": "mage", "m": "mage",
    "berserk": "berserk", "bers": "berserk", "b": "berserk",
    "archer": "archer", "arch": "archer", "a": "archer",
    "tank": "tank", "t": "tank",
}

CLASS_LABELS = {
    "healer":  "🌸 Healer",
    "mage":    "🔵 Mage",
    "berserk": "🔴 Berserk",
    "archer":  "🟡 Archer",
    "tank":    "🟢 Tank",
}

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

def xp_for_level(target: float) -> float:
    if target <= 50:
        needed = 0
        for i in range(min(int(target), 50)):
            needed += SKILL_XP_TABLE[i]
        return needed
    return TOTAL_XP_TO_50 + (target - 50) * 200_000_000

def runs_needed(current_xp: float, target: float) -> int:
    target_xp = xp_for_level(target)
    xp_needed = max(0, target_xp - current_xp)
    if xp_needed == 0:
        return 0
    return -(-int(xp_needed) // MAIN_CLASS_XP)  # ceil division

async def classcalc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "❗ Использование: `/classcalc <ник> <класс> <уровень>`\n\n"
            "Пример: `/classcalc Technoblade tank 50`\n"
            "Классы: healer, mage, berserk, archer, tank",
            parse_mode="Markdown"
        )
        return

    username = context.args[0]
    class_input = context.args[1].lower()
    try:
        target_level = float(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ Уровень должен быть числом. Пример: `50` или `55`", parse_mode="Markdown")
        return

    class_key = CLASS_ALIASES.get(class_input)
    if not class_key:
        await update.message.reply_text(
            "❌ Неизвестный класс!\nДоступные: `healer`, `mage`, `berserk`, `archer`, `tank`",
            parse_mode="Markdown"
        )
        return

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

    current_xp = player_classes.get(class_key, {}).get("experience", 0)
    current_level = xp_to_level(current_xp)
    runs = runs_needed(current_xp, target_level)
    label = CLASS_LABELS[class_key]

    if runs == 0:
        await msg.edit_text(
            f"{label} *{username}* `[{cute_name}]`\n\n"
            f"Текущий уровень: *{current_level:.2f}*\n"
            f"✅ Цель *{target_level:.0f}* уже достигнута!",
            parse_mode="Markdown"
        )
        return

    lines = [
        f"{label} *{username}* `[{cute_name}]`\n",
        f"Текущий уровень: *{current_level:.2f}*",
        f"Цель: *{target_level:.0f}*",
        f"\n🏃 Ранов M7 как основной: *{runs:,}*",
    ]

    await msg.edit_text("\n".join(lines), parse_mode="Markdown")