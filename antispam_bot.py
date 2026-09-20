"""Mustaqil anti-spam bot — faqat guruh moderatsiyasi bilan shug'ullanadi.

Bu fayl `main.py` dan farqli o'laroq Anthropic AI qismiga umuman bog'liq emas:
unga faqat TELEGRAM_BOT_TOKEN kerak. Aniqlash mantig'i `antispam.py` modulidan
olinadi.

Ishga tushirish:
    pip install -r requirements.txt
    python antispam_bot.py

Token .env faylida yoki muhit o'zgaruvchisida topilmasa, bot uni ishga
tushganda so'raydi va .env fayliga o'zi saqlaydi.

MUHIM: har bir Telegram boti uchun ALOHIDA token ishlating. Bitta token ikki
xil dasturda (masalan, eski do'kon/buyurtma boti va shu anti-spam boti)
ishlatilsa, ular bir-birining xabarlarini "tortib oladi" va bot go'yo boshqa
vazifani bajarayotgandek ko'rinadi. Shuning uchun bu bot ishga tushganda
o'zining kimligini va webhook holatini logga aniq yozadi.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.error import InvalidToken, NetworkError
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import antispam

load_dotenv()

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
SPAM_SCORE_THRESHOLD = int(os.environ.get("SPAM_SCORE_THRESHOLD", "3"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=LOG_LEVEL,
)
logger = logging.getLogger(__name__)


def ensure_token() -> str:
    """Tokenni topadi; topilmasa foydalanuvchidan so'rab, .env ga saqlaydi.

    Shu tufayli botni ishga tushirish uchun qo'lda .env yaratish yoki muhit
    o'zgaruvchisi bilan ovora bo'lish shart emas.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        return token

    print("\nTELEGRAM_BOT_TOKEN topilmadi.")
    print("@BotFather bergan bot tokenini kiriting va Enter bosing:")
    token = input("TOKEN: ").strip()
    if not token:
        raise SystemExit("Token kiritilmadi. Bot ishga tushmadi.")

    env_path = Path(__file__).resolve().parent / ".env"
    # encoding="utf-8" BOM yozmaydi: BOM bo'lsa python-dotenv birinchi kalitni
    # noto'g'ri o'qiydi va token keyingi safar yana "topilmadi" bo'lib chiqadi.
    env_path.write_text(
        f"TELEGRAM_BOT_TOKEN={token}\nSPAM_SCORE_THRESHOLD=3\nLOG_LEVEL=INFO\n",
        encoding="utf-8",
    )
    print(f"Saqlandi: {env_path}")
    print("Keyingi safar token qaytadan so'ralmaydi.\n")
    return token


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Men guruh moderatori botiman.\n\n"
        "Meni guruhingizga qo'shing va ADMIN qiling — quyidagi huquqlar bilan:\n"
        "• Xabarlarni o'chirish (Delete messages)\n"
        "• Foydalanuvchilarni bloklash (Ban users)\n\n"
        "Shundan so'ng men guruhdagi spam, reklama va 18+ mazmunli "
        "xabarlarni avtomatik o'chirib, ularni yuborgan profillarni bloklayman."
    )


async def _log_identity(application: Application) -> None:
    """Bot ishga tushishi bilan QAYSI bot akkaunti ekanini va oldin webhook
    o'rnatilgan-o'rnatilmaganini logga yozadi.

    Bu tekshiruv bitta tokenni ikki xil dasturda ishlatishdan kelib chiqadigan
    eng chalkash xatoni darhol ko'rsatadi: agar token boshqa (masalan, eski
    deploy qilingan) botga tegishli bo'lsa, quyidagi logdagi username siz
    kutgan botnikidan boshqa bo'ladi.
    """
    me = await application.bot.get_me()
    logger.info("Ishga tushdi: @%s (id=%s, ism=%s)", me.username, me.id, me.first_name)

    webhook_info = await application.bot.get_webhook_info()
    if webhook_info.url:
        logger.warning(
            "DIQQAT: bu tokenda webhook o'rnatilgan edi (%s). Demak shu token "
            "boshqa bir dasturda (boshqa serverda) ham ishlatilmoqda. Polling "
            "boshlanishi bilan u webhook o'chiriladi, lekin o'sha boshqa dastur "
            "qayta ishga tushsa, webhookni qaytadan o'rnatib, xabarlarni o'ziga "
            "tortib oladi. Bu bot uchun @BotFather'dan ALOHIDA token oling.",
            webhook_info.url,
        )


def main() -> None:
    token = ensure_token()

    antispam.SPAM_SCORE_THRESHOLD = SPAM_SCORE_THRESHOLD

    application = (
        Application.builder().token(token).post_init(_log_identity).build()
    )

    # Guruh/superguruh xabarlarini tekshiruvchi asosiy handler.
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & (filters.TEXT | filters.CAPTION),
            antispam.moderate_group_message,
        )
    )
    # Shaxsiy chatda botning qaysi bot ekanini tasdiqlash uchun.
    application.add_handler(CommandHandler("start", start, filters.ChatType.PRIVATE))

    logger.info("Anti-spam bot polling rejimida (spam_threshold=%s)...", SPAM_SCORE_THRESHOLD)
    # drop_pending_updates=True — eski, navbatda turib qolgan xabarlar qayta
    # ishlanmasin (aks holda bot ishga tushishi bilan eski xabarlar uchun
    # ham chora ko'rishi mumkin).
    try:
        application.run_polling(
            allowed_updates=[Update.MESSAGE, Update.EDITED_MESSAGE],
            drop_pending_updates=True,
        )
    except InvalidToken:
        raise SystemExit(
            "\nXATO: token yaroqsiz.\n"
            ".env faylidagi TELEGRAM_BOT_TOKEN ni tekshiring yoki @BotFather'dan "
            "yangi token oling.\n"
        )
    except NetworkError as exc:
        raise SystemExit(
            f"\nXATO: Telegram serveriga ulanib bo'lmadi.\n{exc}\n\n"
            "Internet aloqasini tekshiring. Agar Telegram bloklangan bo'lsa, "
            "VPN yoki proxy kerak bo'ladi.\n"
        )


if __name__ == "__main__":
    main()
