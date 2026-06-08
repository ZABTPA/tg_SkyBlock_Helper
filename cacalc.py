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

MAIN_CLASS_XP = 420_000   # XP за M7 для основного класса
PASSIVE_CLASS_XP = 105_000  # XP за M7 для остальных классов

def xp_to_level_and_remaining(xp: float) -> tuple:
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
        total_level = 50 + overflow / 200_000_000
        remaining_to_next = 200_000_000 - (overflow % 200_000_000)
        return total_level, remaining_to_next
    next_xp = SKILL_XP_TABLE[level] if level < len(SKILL_XP_TABLE) else 200_000_000
    return level + remaining / next_xp, next_xp - remaining

def runs_needed(xp_needed: float, xp_per_run: float) -> int:
    return max(0, int((xp_needed + xp_per_run - 1) // xp_per_run))

async def cacalc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❗ Укажи ник и цель!\n"
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

    class_names = {
        "healer":  "🌸 Healer",
        "mage":    "🔵 Mage",
        "berserk": "🔴 Berserk",
        "archer":  "🟡 Archer",
        "tank":    "🟢 Tank",
    }

    # Считаем XP нужный до цели для каждого класса
    target_xp = sum(SKILL_XP_TABLE[:50]) + max(0, (target_ca - 50)) * 200_000_000

    lines = [f"🧮 Калькулятор CA *{username}* `[{cute_name}]`\n📊 Цель: *CA {target_ca:.0f}*\n"]

    total_runs_main = []
    total_runs_passive = []

    for key, label in class_names.items():
        xp = player_classes.get(key, {}).get("experience", 0)
        level, remaining = xp_to_level_and_remaining(xp)

        # XP нужно до цели
        if xp >= target_xp:
            xp_needed = 0
        else:
            xp_needed = target_xp - xp

        runs_main = runs_needed(xp_needed, MAIN_CLASS_XP)
        runs_passive = runs_needed(xp_needed, PASSIVE_CLASS_XP)

        total_runs_main.append(runs_main)
        total_runs_passive.append(runs_passive)

        lines.append(f"{label}: *{level:.2f}* → нужно *{runs_main:,}* ранов M7 _(как основной)_")

    # CA = среднее всех классов
    # Для CA50 нужно чтобы каждый класс был 50
    # Максимальное кол-во ранов = сколько нужно самому слабому классу как основному
    max_runs = max(total_runs_main)
    lines.append(f"\n⭐ До CA *{target_ca:.0f}*: ~*{max_runs:,}* ранов M7")
    lines.append(f"💡 Это если качать самый отстающий класс основным каждый ран")

    await msg.edit_text("\n".join(lines), parse_mode="Markdown")