"""Mustaqil anti-spam bot — faqat guruh moderatsiyasi bilan shug'ullanadi.

Bu fayl `main.py` dan farqli o'laroq Anthropic AI qismiga umuman bog'liq emas:
unga faqat TELEGRAM_BOT_TOKEN kerak. Aniqlash mantig'i `antispam.py` modulidan
olinadi.

Ishga tushirish:
    pip install -r requirements.txt
    python antispam_bot.py

Sinov rejimida ishga tushirish (admin himoyasi ishlamaydi, hech kim
bloklanmaydi - spam xabar faqat o'chiriladi):
    python antispam_bot.py --test

Token .env faylida yoki muhit o'zgaruvchisida topilmasa, bot uni ishga
tushganda so'raydi va .env fayliga o'zi saqlaydi.

MUHIM: har bir Telegram boti uchun ALOHIDA token ishlating. Bitta token ikki
xil dasturda (masalan, eski do'kon/buyurtma boti va shu anti-spam boti)
ishlatilsa, ular bir-birining xabarlarini "tortib oladi" va bot go'yo boshqa
vazifani bajarayotgandek ko'rinadi. Shuning uchun bu bot ishga tushganda
o'zining kimligini va webhook holatini logga aniq yozadi.
"""

from __future__ import annotations

import argparse
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
TEST_MODE = os.environ.get("ANTISPAM_TEST_MODE", "").strip().lower() in ("1", "true", "yes")

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


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Guruh ichida yozilganda botning o'sha guruhdagi holatini ko'rsatadi.

    Bitta buyruq bilan "bot shu yerdami, admin bo'lganmi, o'chira oladimi"
    degan savollarning hammasiga javob beradi.
    """
    chat = update.effective_chat
    me = await context.bot.get_me()
    member = await context.bot.get_chat_member(chat.id, context.bot.id)

    lines = [
        f"Bot: @{me.username}",
        f"Guruh: {chat.type} (id={chat.id})",
        f"Holat: {member.status}",
    ]

    if member.status == "administrator":
        can_delete = "HA" if member.can_delete_messages else "YO'Q"
        can_ban = "HA" if member.can_restrict_members else "YO'Q"
        lines.append(f"Xabar o'chirish: {can_delete}")
        lines.append(f"Bloklash: {can_ban}")
    else:
        lines.append("DIQQAT: bot ADMIN EMAS - hech narsa o'chira olmaydi.")

    if chat.type == "group":
        lines.append(
            "DIQQAT: bu oddiy guruh. Superguruhga aylantiring: "
            "sozlamalar -> 'Chat history for new members' -> 'Visible'."
        )

    lines.append(f"Spam chegarasi: {antispam.SPAM_SCORE_THRESHOLD}")
    if antispam.TEST_MODE:
        lines.append("TEST REJIMI yoqilgan: hech kim bloklanmaydi.")

    # effective_message ishlatiladi: kanalga yozilgan buyruqda update.message
    # bo'sh bo'ladi va bot xato bilan to'xtardi.
    await update.effective_message.reply_text("\n".join(lines))


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
    parser = argparse.ArgumentParser(description="Telegram guruhlari uchun anti-spam bot")
    parser.add_argument(
        "--test",
        action="store_true",
        help="sinov rejimi: admin himoyasi ishlamaydi va hech kim bloklanmaydi "
             "(spam xabar faqat o'chiriladi). Batafsil logni ham yoqadi",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="guruhda ko'rilgan HAR BIR xabarni va uning ballini logga yozadi",
    )
    args = parser.parse_args()

    # Rejim buyruq qatoridagi --test yoki .env dagi ANTISPAM_TEST_MODE orqali
    # yoqiladi; ikkalasidan biri yetarli.
    test_mode = TEST_MODE or args.test

    token = ensure_token()

    antispam.SPAM_SCORE_THRESHOLD = SPAM_SCORE_THRESHOLD
    antispam.TEST_MODE = test_mode
    # Sinov rejimida batafsil log har doim kerak bo'ladi.
    antispam.VERBOSE = args.verbose or test_mode

    if test_mode:
        logger.warning("=" * 60)
        logger.warning("TEST REJIMI YOQILGAN")
        logger.warning("  - admin va guruh egasi himoyasi ISHLAMAYDI")
        logger.warning("  - spam xabar faqat O'CHIRILADI, hech kim BLOKLANMAYDI")
        logger.warning("  Normal rejimga qaytish: --test siz ishga tushiring")
        logger.warning("=" * 60)

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
    # Guruh ichida yozilsa, botning o'sha guruhdagi holatini ko'rsatadi.
    application.add_handler(CommandHandler("status", status))

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
