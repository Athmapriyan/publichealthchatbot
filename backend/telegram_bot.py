"""
Telegram bot frontend for the Public Health Chatbot.

Runs as a SEPARATE process from the FastAPI backend — this script is a thin
client that calls your existing backend's REST API (/chat, /risk-assessment,
/misinformation-check) over HTTP. It does not re-implement any logic; it's
just a Telegram-shaped UI layer on top of main.py.

Run (in a separate terminal, with the FastAPI backend already running):
    python -m backend.telegram_bot

Requires in .env:
    TELEGRAM_BOT_TOKEN=...          (from @BotFather)
    BACKEND_BASE_URL=http://127.0.0.1:8000   (default, change for deployment)
"""
from __future__ import annotations
import logging
import os
import httpx

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("telegram_bot")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")

# Per-chat language preference, in-memory only (resets if the bot restarts).
# Fine for a prototype; swap for persistence.py / a DB later if needed.
USER_LANGUAGE: dict[int, str] = {}

LANG_LABELS = {
    "en": "English", "hi": "हिन्दी Hindi", "bn": "বাংলা Bengali",
    "te": "తెలుగు Telugu", "mr": "मराठी Marathi", "ta": "தமிழ் Tamil",
    "gu": "ગુજરાતી Gujarati", "ur": "اردو Urdu", "kn": "ಕನ್ನಡ Kannada",
    "or": "ଓଡ଼ିଆ Odia", "ml": "മലയാളം Malayalam", "pa": "ਪੰਜਾਬੀ Punjabi",
}
WELCOME_TEXT = (
    "🩺 *Odisha Public Health Chatbot*\n\n"
    "Ask me about diseases, symptoms, prevention, or check if a health message "
    "you received is true.\n\n"
    "Commands:\n"
    "/language — choose English / Hindi / Odia\n"
    "/risk — structured symptom risk check\n"
    "/checkclaim <message> — verify a health claim/rumour\n"
    "/help — show this message again\n\n"
    "⚠️ This bot gives general awareness information only. It is *not* a substitute "
    "for professional medical advice, diagnosis, or treatment."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")


async def language_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"lang:{code}")]
        for code, label in LANG_LABELS.items()
    ]
    await update.message.reply_text(
        "Choose your language:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    code = query.data.split(":", 1)[1]
    USER_LANGUAGE[query.message.chat_id] = code
    await query.edit_message_text(f"Language set to {LANG_LABELS.get(code, code)}. Ask me anything!")


async def checkclaim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    claim = " ".join(context.args) if context.args else None
    if not claim:
        await update.message.reply_text(
            "Usage: /checkclaim <paste the claim or forwarded message here>"
        )
        return
    await update.message.chat.send_action("typing")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{BACKEND_BASE_URL}/misinformation-check", json={"claim": claim}
            )
            resp.raise_for_status()
            data = resp.json()
        verdict_emoji = {
            "supported": "✅", "misleading": "⚠️", "unsupported": "❓",
            "false": "❌", "insufficient_evidence": "❓",
        }.get(data["verdict"], "❓")
        text = (
            f"{verdict_emoji} *Verdict: {data['verdict'].replace('_', ' ').title()}*\n\n"
            f"{data['explanation']}\n"
        )
        if data.get("sources"):
            text += "\n*Sources:*\n" + "\n".join(f"• {s['source']}" for s in data["sources"])
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.exception("checkclaim failed")
        await update.message.reply_text(
            "⚠️ Sorry, I couldn't check that claim right now. Please try again shortly."
        )


async def risk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "For a structured risk check, please describe your symptoms in a normal message "
        "(e.g. \"I'm an adult with high fever for 3 days and joint pain, temperature 39°C\") "
        "and I'll do my best to assess it conversationally. "
        "A dedicated step-by-step risk form is on the roadmap for this bot."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_text = update.message.text
    language = USER_LANGUAGE.get(chat_id, "en")

    await update.message.chat.send_action("typing")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{BACKEND_BASE_URL}/chat",
                json={"message": user_text, "language": language},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.exception("chat request failed")
        await update.message.reply_text(
            "⚠️ Sorry, I'm temporarily unable to reach the health information service. "
            "Please try again shortly, or consult a qualified healthcare professional."
        )
        return

    if data.get("is_emergency"):
        await update.message.reply_text(f"🚨 {data['response']}")
        return

    reply = data["response"]
    if data.get("sources"):
        reply += "\n\n*Sources:*\n" + "\n".join(
            f"• [{s['source']}]({s['url']})" for s in data["sources"] if s.get("url")
        )
    reply += f"\n\n_{data['disclaimer']}_"

    # Telegram message limit is 4096 chars; trim defensively.
    if len(reply) > 4000:
        reply = reply[:3990] + "…"

    try:
        await update.message.reply_text(reply, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception:
        # Markdown parsing can fail on unescaped special characters from the LLM —
        # fall back to plain text rather than silently dropping the reply.
        await update.message.reply_text(reply)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Telegram bot error: %s", context.error, exc_info=context.error)


def build_app() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. Get one from @BotFather on Telegram and add it to .env"
        )
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("language", language_cmd))
    app.add_handler(CommandHandler("checkclaim", checkclaim_cmd))
    app.add_handler(CommandHandler("risk", risk_cmd))
    app.add_handler(CallbackQueryHandler(language_callback, pattern=r"^lang:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    return app


def main():
    app = build_app()
    logger.info("Starting Telegram bot (polling mode), backend at %s", BACKEND_BASE_URL)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
