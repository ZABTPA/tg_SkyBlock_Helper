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

SKILL_XP_TABLE = [
    50, 75, 110, 160, 230, 330, 470, 670, 950, 1340,
    1890, 2665, 3760, 5260, 7380, 10300, 14400, 20000, 27600, 38000,
    52500, 71500, 97000, 132000, 180000, 243000, 328000, 445000, 600000, 800000,
    1065000, 1410000, 1900000, 2500000, 3300000, 4300000, 5600000, 7200000, 9200000, 12000000,
    15000000, 19000000, 24000000, 30000000, 38000000, 48000000, 60000000, 75000000, 93000000, 116250000
]

def cata_xp_to_level(xp: float) -> tuple:
    level = 0
    remaining = xp
    for needed in CATACOMBS_XP_TABLE:
        if remaining >= needed:
            remaining -= needed
            level += 1
        else:
            break
    if level >= 50:
        overflow = xp - sum(CATACOMBS_XP_TABLE)
        overflow_levels = overflow / 200_000_000
        total_level = 50 + overflow_levels
        progress = overflow % 200_000_000
        return total_level, progress
    next_xp = CATACOMBS_XP_TABLE[level] if level < len(CATACOMBS_XP_TABLE) else 200_000_000
    decimal = remaining / next_xp
    return level + decimal, remaining

def class_xp_to_level(xp: float) -> tuple:
    level = 0
    remaining = xp
    for needed in SKILL_XP_TABLE:
        if remaining >= needed:
            remaining -= needed
            level += 1
        else:
            break
    if level >= 50:
        overflow = xp - sum(SKILL_XP_TABLE)
        overflow_levels = overflow / 200_000_000
        total_level = 50 + overflow_levels
        progress = overflow % 200_000_000
        return total_level, progress
    next_xp = SKILL_XP_TABLE[level] if level < len(SKILL_XP_TABLE) else 200_000_000
    decimal = remaining / next_xp
    return level + decimal, remaining

async def dungeons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи ник!\nПример: `/dungeons Technoblade`\nС профилем: `/dungeons Technoblade Mango`", parse_mode="Markdown")
        return

    username = context.args[0]
    profile_name = context.args[1].lower() if len(context.args) > 1 else None

    msg = await update.message.reply_text(f"🔍 Ищу *{username}*...", parse_mode="Markdown")

    uuid = get_uuid(username)
    if not uuid:
        await msg.edit_text("❌ Игрок не найден. Проверь ник.")
        return

    data = get_profiles(uuid)
    if not data:
        await msg.edit_text("❌ Ошибка Hypixel API. Попробуй позже.")
        return

    profiles = data.get("profiles", [])
    if not profiles:
        await msg.edit_text("❌ SkyBlock профили не найдены.")
        return

    if profile_name:
        profile = next(
            (p for p in profiles if p.get("cute_name", "").lower() == profile_name),
            None
        )
        if not profile:
            names = ", ".join(p.get("cute_name", "?") for p in profiles)
            await msg.edit_text(f"❌ Профиль *{profile_name}* не найден.\nДоступные: `{names}`", parse_mode="Markdown")
            return
    else:
        profile = next((p for p in profiles if p.get("selected")), None)
        if not profile:
            profile = profiles[0]

    cute_name = profile.get("cute_name", "?")
    member = profile.get("members", {}).get(uuid, {})

    if not member:
        await msg.edit_text("❌ Данные игрока в этом профиле не найдены.")
        return

    dungeons = member.get("dungeons", {})
    dungeon_types = dungeons.get("dungeon_types", {})
    catacombs = dungeon_types.get("catacombs", {})
    player_classes = dungeons.get("player_classes", {})

    cata_xp = catacombs.get("experience", 0)
    cata_level, cata_progress = cata_xp_to_level(cata_xp)

    secrets = member.get("player_stats", {}).get("dungeons", {}).get("secrets_found", 0)

    class_names = {
        "healer":  "💚 Healer",
        "mage":    "🔵 Mage",
        "berserk": "🔴 Berserk",
        "archer":  "🟡 Archer",
        "tank":    "🟤 Tank",
    }

    lines = [f"⚔️ Катакомбы *{username}* `[{cute_name}]`:\n"]

    if cata_level >= 50:
        lines.append(f"🏰 Catacombs: *{cata_level:.2f}* _(до след: {int(200_000_000 - cata_progress):,} XP)_\n")
    else:
        lines.append(f"🏰 Catacombs: *{cata_level:.2f}* _(XP: {int(cata_xp):,})_\n")

    lines.append(f"🔑 Секретки: *{int(secrets):,}*\n")
    lines.append("👤 Классы:")

    for key, label in class_names.items():
        class_data = player_classes.get(key, {})
        xp = class_data.get("experience", 0)
        level, progress = class_xp_to_level(xp)
        if level >= 50:
            lines.append(f"{label}: *{level:.2f}* _(до след: {int(200_000_000 - progress):,} XP)_")
        else:
            lines.append(f"{label}: *{level:.2f}* _(XP: {int(xp):,})_")

    await msg.edit_text("\n".join(lines), parse_mode="Markdown")