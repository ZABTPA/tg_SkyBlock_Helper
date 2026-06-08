from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from api.mojang import get_uuid
from api.hypixel import get_profiles
import datetime

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

def get_total_runs(catacombs: dict, master: bool = False) -> int:
    tier_completions = catacombs.get("tier_completions", {})
    return sum(tier_completions.values())

def get_daily_runs(catacombs: dict, master: bool = False) -> dict:
    # Время сброса — 4:00 утра по Екатеринбургу (UTC+5)
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5)))
    reset_time = now.replace(hour=4, minute=0, second=0, microsecond=0)
    if now < reset_time:
        reset_time -= datetime.timedelta(days=1)
    reset_timestamp = int(reset_time.timestamp() * 1000)

    floor_key = "master_catacombs_completions" if master else "catacombs_completions"
    completions = catacombs.get(floor_key, {})

    daily = {}
    for floor, runs in completions.items():
        daily_count = sum(1 for t in runs if t >= reset_timestamp)
        if daily_count > 0:
            daily[floor] = daily_count
    return daily

def build_main_text(username, cute_name, cata_level, cata_progress, cata_xp, secrets, player_classes, class_names):
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

    return "\n".join(lines)

def build_runs_text(username, cute_name, catacombs, master_catacombs):
    lines = [f"🏃 Раны *{username}* `[{cute_name}]`:\n"]

    # Обычный режим
    normal_total = get_total_runs(catacombs)
    lines.append(f"⚔️ Обычный режим: *{normal_total:,}* ранов")
    tier_completions = catacombs.get("tier_completions", {})
    for floor, count in sorted(tier_completions.items()):
        floor_name = "Entrance" if floor == "0" else f"F{floor}"
        lines.append(f"  {floor_name}: *{count:,}*")

    lines.append("")

    # Мастер мод
    master_total = get_total_runs(master_catacombs)
    lines.append(f"💀 Мастер мод: *{master_total:,}* ранов")
    master_completions = master_catacombs.get("tier_completions", {})
    for floor, count in sorted(master_completions.items()):
        lines.append(f"  M{floor}: *{count:,}*")

    return "\n".join(lines)

def build_daily_text(username, cute_name, catacombs, master_catacombs):
    lines = [f"📅 Дейли раны *{username}* `[{cute_name}]` _(сброс в 4:00 по Екб)_:\n"]

    daily_normal = get_daily_runs(catacombs)
    daily_master = get_daily_runs(master_catacombs, master=True)

    if daily_normal:
        lines.append("⚔️ Обычный режим:")
        for floor, count in sorted(daily_normal.items()):
            floor_name = "Entrance" if floor == "0" else f"F{floor}"
            lines.append(f"  {floor_name}: *{count}*")
    else:
        lines.append("⚔️ Обычный режим: *0* ранов сегодня")

    lines.append("")

    if daily_master:
        lines.append("💀 Мастер мод:")
        for floor, count in sorted(daily_master.items()):
            lines.append(f"  M{floor}: *{count}*")
    else:
        lines.append("💀 Мастер мод: *0* ранов сегодня")

    return "\n".join(lines)

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
    master_catacombs = dungeon_types.get("master_catacombs", {})
    player_classes = dungeons.get("player_classes", {})

    cata_xp = catacombs.get("experience", 0)
    cata_level, cata_progress = cata_xp_to_level(cata_xp)
    secrets = member.get("player_stats", {}).get("dungeons", {}).get("secrets_found", 0)

    class_names = {
        "healer":  "🌸 Healer",
        "mage":    "🔵 Mage",
        "berserk": "🔴 Berserk",
        "archer":  "🟡 Archer",
        "tank":    "🟢 Tank",
    }

    # Сохраняем данные в context для кнопок
    context.user_data["dungeons"] = {
        "username": username,
        "cute_name": cute_name,
        "cata_level": cata_level,
        "cata_progress": cata_progress,
        "cata_xp": cata_xp,
        "secrets": secrets,
        "player_classes": player_classes,
        "class_names": class_names,
        "catacombs": catacombs,
        "master_catacombs": master_catacombs,
    }

    text = build_main_text(username, cute_name, cata_level, cata_progress, cata_xp, secrets, player_classes, class_names)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏃 Runs", callback_data="dungeons_runs"),
            InlineKeyboardButton("📅 Daily", callback_data="dungeons_daily"),
            InlineKeyboardButton("🏰 Главная", callback_data="dungeons_main"),
        ]
    ])

    await msg.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def dungeons_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = context.user_data.get("dungeons")
    if not data:
        await query.edit_message_text("❌ Данные устарели. Запроси заново через /dungeons.")
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏃 Runs", callback_data="dungeons_runs"),
            InlineKeyboardButton("📅 Daily", callback_data="dungeons_daily"),
            InlineKeyboardButton("🏰 Главная", callback_data="dungeons_main"),
        ]
    ])

    if query.data == "dungeons_main":
        text = build_main_text(
            data["username"], data["cute_name"], data["cata_level"],
            data["cata_progress"], data["cata_xp"], data["secrets"],
            data["player_classes"], data["class_names"]
        )
    elif query.data == "dungeons_runs":
        text = build_runs_text(data["username"], data["cute_name"], data["catacombs"], data["master_catacombs"])
    elif query.data == "dungeons_daily":
        text = build_daily_text(data["username"], data["cute_name"], data["catacombs"], data["master_catacombs"])
    else:
        return

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)