from telegram import Update
from telegram.ext import ContextTypes
from api.mojang import get_uuid
from api.hypixel import get_profiles

CATACOMBS_XP_TABLE = [
    50, 75, 110, 160, 230, 330, 470, 670, 950, 1340,
    1890, 2665, 3760, 5260, 7380, 10300, 14400, 20000, 27600, 38000,
    52500, 71500, 97000, 132000, 180000, 243000, 328000, 445000, 600000, 800000,
    1065000, 1410000, 1900000, 2500000, 3300000, 4300000, 5600000, 7200000, 9200000, 12000000,
    15000000, 19000000, 24000000, 30000000, 38000000, 48000000, 60000000, 75000000, 93000000, 116250000
]

CATA_XP_PER_RUN = 504_001
TOTAL_XP_TO_50 = sum(CATACOMBS_XP_TABLE)

def xp_to_level(xp: float) -> float:
    level = 0
    remaining = xp
    for needed in CATACOMBS_XP_TABLE:
        if remaining >= needed:
            remaining -= needed
            level += 1
        else:
            break
    if level >= 50:
        overflow = xp - TOTAL_XP_TO_50
        return 50 + overflow / 200_000_000
    next_xp = CATACOMBS_XP_TABLE[level] if level < len(CATACOMBS_XP_TABLE) else 200_000_000
    return level + remaining / next_xp

def xp_for_level(target: float) -> float:
    if target <= 50:
        return sum(CATACOMBS_XP_TABLE[:int(target)])
    return TOTAL_XP_TO_50 + (target - 50) * 200_000_000

def runs_needed(current_xp: float, target: float) -> int:
    target_xp = xp_for_level(target)
    xp_needed = max(0, target_xp - current_xp)
    if xp_needed == 0:
        return 0
    return -(-int(xp_needed) // CATA_XP_PER_RUN)

async def catacalc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "❗ Использование: `/catacalc <ник> <уровень>`\n\n"
            "Пример: `/catacalc Technoblade 50`\n"
            "Или: `/catacalc Technoblade 60`",
            parse_mode="Markdown"
        )
        return

    username = context.args[0]
    try:
        target_level = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Уровень должен быть числом. Пример: `50` или `60`", parse_mode="Markdown")
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
    dungeon_types = dungeons.get("dungeon_types", {})
    catacombs = dungeon_types.get("catacombs", {})

    current_xp = catacombs.get("experience", 0)
    current_level = xp_to_level(current_xp)
    runs = runs_needed(current_xp, target_level)

    if runs == 0:
        await msg.edit_text(
            f"🏰 Catacombs *{username}* `[{cute_name}]`\n\n"
            f"Текущий уровень: *{current_level:.2f}*\n"
            f"✅ Цель *{target_level:.0f}* уже достигнута!",
            parse_mode="Markdown"
        )
        return

    lines = [
        f"🏰 Catacombs *{username}* `[{cute_name}]`\n",
        f"Текущий уровень: *{current_level:.2f}*",
        f"Цель: *{target_level:.0f}*",
        f"\n🏃 Ранов M7: *{runs:,}*",
    ]

    await msg.edit_text("\n".join(lines), parse_mode="Markdown")