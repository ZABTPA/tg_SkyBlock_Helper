from telegram import Update
from telegram.ext import ContextTypes
from api.mojang import get_uuid
from api.hypixel import get_profiles

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

async def skills_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи ник!\nПример: `/skills Technoblade`\nС профилем: `/skills Technoblade Mango`", parse_mode="Markdown")
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
            await msg.edit_text(f"❌ Профиль *{profile_name}* не найден.\nДоступные профили: `{names}`", parse_mode="Markdown")
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

    skills = parse_skills(member)
    levels = [v["level"] for v in skills.values()]
    avg = sum(levels) / len(levels)

    lines = [f"📊 Скиллы *{username}* `[{cute_name}]`:\n"]
    for skill_name, val in skills.items():
        lines.append(f"{skill_name}: *{val['level']}* _(XP: {int(val['xp']):,})_")

    lines.append(f"\n⭐ Средний уровень: *{avg:.1f}*")

    if all(v["xp"] == 0 for v in skills.values()):
        lines.append("\n⚠️ XP везде 0 — игрок отключил Skills API в настройках профиля.")

    all_profiles = ", ".join(p.get("cute_name", "?") for p in profiles)
    lines.append(f"\n📋 Все профили: `{all_profiles}`")
    lines.append(f"💡 Другой профиль: `/skills {username} <название>`")

    await msg.edit_text("\n".join(lines), parse_mode="Markdown")