import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

from telegram import BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from config import TG_TOKEN
from handlers.start import start_handler
from handlers.skills import skills_handler
from handlers.dungeons import dungeons_handler, dungeons_callback

async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start",   "🏠 Главное меню"),
        BotCommand("skills",  "⚔️ Скиллы игрока"),
        BotCommand("dungeons","🏰 Катакомбы и классы"),
    ])

def main():
    app = ApplicationBuilder().token(TG_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("skills", skills_handler))
    app.add_handler(CommandHandler("dungeons", dungeons_handler))
    app.add_handler(CallbackQueryHandler(dungeons_callback, pattern="^dg_"))

    app.post_init = set_commands

    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()