from telegram import Update
from telegram.ext import ContextTypes

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я *SkyBlock Helper Bot*\n\n"
        "📌 Команды:\n"
        "/skills `<ник>` — уровни скиллов\n"
        "/catacalc `<ник> <уровень>` — catacombs калькулятор\n"
        "/cacalc `<ник> <уровень>` — class average калькулятор\n"
        "/classcalc `<ник> <класс> <уровень>` — калькулятор одного класса\n"
        "/dungeons `<ник>` — уровень catacombs\n\n"
        "Пример: `/skills ZABTPA`",
        parse_mode="Markdown"
    )