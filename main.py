"""Anthropic Claude bilan ishlaydigan Telegram bot."""

import logging
import os
import re

import anthropic
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import antispam
from system_prompt import SYSTEM_PROMPT

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")
ANTHROPIC_MAX_TOKENS = int(os.environ.get("ANTHROPIC_MAX_TOKENS", "1024"))
ANTHROPIC_EFFORT = os.environ.get("ANTHROPIC_EFFORT", "medium")
MAX_HISTORY_MESSAGES = int(os.environ.get("MAX_HISTORY_MESSAGES", "20"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
SPAM_SCORE_THRESHOLD = int(os.environ.get("SPAM_SCORE_THRESHOLD", "3"))

TELEGRAM_MESSAGE_LIMIT = 4096

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=LOG_LEVEL,
)
logger = logging.getLogger(__name__)

anthropic_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

# chat_id -> [{"role": "user"|"assistant", "content": str}, ...]
conversation_history: dict[int, list[dict]] = {}


def trim_history(history: list[dict]) -> None:
    if len(history) > MAX_HISTORY_MESSAGES:
        del history[: len(history) - MAX_HISTORY_MESSAGES]
    # Anthropic messages array must start with a "user" turn.
    while history and history[0]["role"] != "user":
        history.pop(0)


def to_telegram_markdown(text: str) -> str:
    """LLM javobidagi **qalin** belgisini Telegram legacy Markdown *qalin* ga o'giradi."""
    return re.sub(r"\*\*(.+?)\*\*", r"*\1*", text, flags=re.DOTALL)


def split_message(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    chunks = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1 or split_at < limit // 2:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:]
    chunks.append(text)
    return chunks


async def send_reply(update: Update, text: str) -> None:
    for chunk in split_message(text):
        try:
            await update.message.reply_text(
                to_telegram_markdown(chunk), parse_mode=ParseMode.MARKDOWN
            )
        except BadRequest:
            # LLM javobidagi formatlash Telegram Markdown parseriga mos kelmasa,
            # oddiy matn sifatida yuboramiz.
            await update.message.reply_text(chunk)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Assalomu alaykum! Men aqlli AI yordamchiman.\n\n"
        "Menga istalgan savolingizni yozing — aniq va tushunarli javob beraman.\n\n"
        "Buyruqlar:\n"
        "/reset — suhbat tarixini tozalash\n"
        "/help — yordam"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Menga oddiy matn ko'rinishida savol yoki topshiriq yozing, men javob beraman.\n\n"
        "/reset — joriy suhbat tarixini tozalaydi va yangi mavzudan boshlaydi.\n"
        "/help — shu xabarni qayta ko'rsatadi."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conversation_history.pop(update.effective_chat.id, None)
    await update.message.reply_text("Suhbat tarixi tozalandi. Yangi mavzudan boshlashingiz mumkin.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    if not user_text:
        return

    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    history = conversation_history.setdefault(chat_id, [])
    history.append({"role": "user", "content": user_text})
    trim_history(history)

    try:
        response = await anthropic_client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=ANTHROPIC_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            output_config={"effort": ANTHROPIC_EFFORT},
            messages=history,
        )
    except anthropic.RateLimitError:
        history.pop()
        await update.message.reply_text(
            "Hozir so'rovlar juda ko'p. Iltimos, bir oz kutib, qaytadan urinib ko'ring."
        )
        return
    except anthropic.APIConnectionError:
        history.pop()
        await update.message.reply_text(
            "Tarmoq bilan bog'lanishda muammo yuz berdi. Birozdan so'ng qayta urinib ko'ring."
        )
        return
    except anthropic.APIStatusError as e:
        history.pop()
        logger.error("Anthropic API xatoligi: %s", e)
        await update.message.reply_text(
            "Kechirasiz, javob tayyorlashda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."
        )
        return
    except Exception:
        history.pop()
        logger.exception("Kutilmagan xatolik yuz berdi")
        await update.message.reply_text(
            "Kutilmagan xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."
        )
        return

    reply_text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()
    if not reply_text:
        reply_text = "Kechirasiz, javob shakllantira olmadim. Savolingizni boshqacha ifodalab ko'ring."

    history.append({"role": "assistant", "content": reply_text})
    trim_history(history)

    await send_reply(update, reply_text)


async def handle_unsupported(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hozircha faqat matnli xabarlarni qayta ishlay olaman. Iltimos, savolingizni yozma ravishda yuboring."
    )


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN muhit o'zgaruvchisi topilmadi (.env faylini tekshiring).")
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY muhit o'zgaruvchisi topilmadi (.env faylini tekshiring).")

    antispam.SPAM_SCORE_THRESHOLD = SPAM_SCORE_THRESHOLD

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Guruh/superguruh xabarlarini spam uchun tekshiruvchi handler — group=-1
    # bilan pastdagi handlerlardan OLDIN ishlaydi va spam aniqlansa
    # ApplicationHandlerStop orqali qolgan handlerlarni (jumladan AI javobini)
    # to'xtatadi. `effective_message` orqali yangi va tahrirlangan
    # xabarlarning ikkalasi ham avtomatik qamrab olinadi (spam-botlar ko'pincha
    # avval zararsiz xabar yozib, keyin uni spamga tahrirlashadi).
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & (filters.TEXT | filters.CAPTION),
            antispam.moderate_group_message,
        ),
        group=-1,
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND, handle_unsupported))

    logger.info(
        "Bot ishga tushmoqda (model=%s, spam_threshold=%s)...",
        ANTHROPIC_MODEL, SPAM_SCORE_THRESHOLD,
    )
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
