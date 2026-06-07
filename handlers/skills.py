from telegram import Update
from telegram.ext import ContextTypes
from api.mojang import get_uuid
from api.hypixel import get_profiles, get_best_profile, parse_skills, xp_to_level

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

    # Если указан конкретный профиль — ищем его
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
        # Берём профиль помеченный как selected или последний активный
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

    # Показываем все профили
    all_profiles = ", ".join(p.get("cute_name", "?") for p in profiles)
    lines.append(f"\n📋 Все профили: `{all_profiles}`")
    lines.append(f"💡 Другой профиль: `/skills {username} <название>`")

    await msg.edit_text("\n".join(lines), parse_mode="Markdown")