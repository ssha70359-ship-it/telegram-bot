"""Anti-spam bot uchun diagnostika skripti — "nega ishlamayapti?" savoliga
aniq javob beradi.

Ishga tushirish (ASOSIY BOTNI TO'XTATIB TURIB!):
    python diagnose.py

Skript ketma-ket tekshiradi:
  1. Token haqiqiyligi va bot kimligi (@username)
  2. Privacy Mode (guruh xabarlarini o'qiy oladimi?) — eng ko'p uchraydigan sabab
  3. Webhook ziddiyati (boshqa dastur shu tokenni egallab turganmi?)
  4. Jonli rejim: guruhga yuborilgan xabarlar botga YETIB KELAYAPTIMI,
     va agar kelsa, spam-filtr ularni qanday baholayapti
  5. Botning o'sha guruhdagi admin huquqlari (o'chirish / bloklash)
"""

from __future__ import annotations

import asyncio
import sys
import time

from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.constants import ChatMemberStatus
from telegram.error import Conflict, InvalidToken, NetworkError, TelegramError

import antispam
from antispam_bot import ensure_token

load_dotenv()

LISTEN_SECONDS = 90


def head(title: str) -> None:
    print(f"\n{'=' * 62}\n{title}\n{'=' * 62}")


async def check_identity(bot: Bot) -> bool:
    """1-2 bosqich: token haqiqiyligi va Privacy Mode."""
    head("1) TOKEN VA BOT KIMLIGI")
    me = await bot.get_me()
    print(f"  Bot: @{me.username}")
    print(f"  ID:  {me.id}")
    print(f"  Ism: {me.first_name}")
    print("\n  >> Bu siz kutgan anti-spam botmi? Agar yo'q bo'lsa — .env dagi")
    print("     TELEGRAM_BOT_TOKEN boshqa botga tegishli.")

    head("2) PRIVACY MODE (guruh xabarlarini o'qish huquqi)")
    if me.can_read_all_group_messages:
        print("  OK — Privacy Mode O'CHIRILGAN. Bot guruhdagi BARCHA xabarlarni ko'radi.")
        return True

    print("  XATO TOPILDI! Privacy Mode YOQILGAN.")
    print("  Bu holatda bot guruhdagi oddiy xabarlarni UMUMAN KO'RMAYDI —")
    print("  faqat /buyruqlar va o'ziga javob berilgan xabarlarni oladi.")
    print("  Shuning uchun spam xabarlar filtrga yetib bormaydi.")
    print("\n  YECHIM (@BotFather orqali):")
    print("    /mybots -> botni tanlang -> Bot Settings -> Group Privacy -> Turn off")
    print("    So'ng botni guruhdan CHIQARIB, QAYTA QO'SHING (bu majburiy!).")
    print("\n  Eslatma: agar bot guruhda ADMIN bo'lsa, u baribir barcha xabarlarni")
    print("  oladi. Shuning uchun botni admin qilish ham bu muammoni hal qiladi.")
    return False


async def check_webhook(bot: Bot) -> None:
    """3-bosqich: webhook ziddiyati."""
    head("3) WEBHOOK HOLATI")
    info = await bot.get_webhook_info()
    if info.url:
        print(f"  XATO TOPILDI! Webhook o'rnatilgan: {info.url}")
        print("  Demak shu tokenni BOSHQA dastur (masalan, eski deploy qilingan")
        print("  bot) ham ishlatmoqda va xabarlarni o'ziga tortib olyapti.")
        print("\n  YECHIM: o'sha boshqa xizmatni to'xtating, yoki bu bot uchun")
        print("  @BotFather'dan alohida yangi token oling.")
    else:
        print("  OK — webhook o'rnatilmagan, polling uchun yo'l ochiq.")

    if info.pending_update_count:
        print(f"  Navbatda turgan xabarlar: {info.pending_update_count}")
    if info.last_error_message:
        print(f"  Telegram'ning oxirgi xatosi: {info.last_error_message}")


async def check_rights(bot: Bot, chat_id: int, chat_title: str) -> None:
    """5-bosqich: botning guruhdagi huquqlari."""
    try:
        member = await bot.get_chat_member(chat_id, bot.id)
    except TelegramError as exc:
        print(f"     [huquqlarni tekshirib bo'lmadi: {exc}]")
        return

    if member.status != ChatMemberStatus.ADMINISTRATOR:
        print(f"     XATO: bot '{chat_title}' guruhida ADMIN EMAS (status={member.status}).")
        print("     Xabarni o'chirish va bloklash uchun admin bo'lishi SHART.")
        return

    can_delete = member.can_delete_messages
    can_ban = member.can_restrict_members
    print(f"     Admin huquqlari: o'chirish={can_delete}, bloklash={can_ban}")
    if not can_delete:
        print("     XATO: 'Delete messages' huquqi yo'q — xabar o'chirilmaydi!")
    if not can_ban:
        print("     XATO: 'Ban users' huquqi yo'q — foydalanuvchi bloklanmaydi!")


async def listen(bot: Bot) -> None:
    """4-5 bosqich: xabarlar yetib kelayotganini jonli kuzatish."""
    head(f"4) JONLI TEKSHIRUV ({LISTEN_SECONDS} soniya)")
    print("  HOZIR guruhingizga test xabar yuboring (boshqa akkauntdan!).")
    print("  Masalan:  Mening profilimga o't, tirnoqlari olingan qiz")
    print("  Kutilmoqda...\n")

    offset = None
    deadline = time.time() + LISTEN_SECONDS
    seen_chats: set[int] = set()
    received = 0

    while time.time() < deadline:
        try:
            updates = await bot.get_updates(
                offset=offset,
                timeout=10,
                allowed_updates=[Update.MESSAGE, Update.EDITED_MESSAGE],
            )
        except Conflict:
            print("  XATO TOPILDI! Conflict — shu token bilan BOSHQA jarayon ham")
            print("  hozir ishlayapti (ehtimol botning o'zi fonda turibdi).")
            print("  Diagnostikadan oldin asosiy botni to'xtating (Ctrl+C).")
            return
        except TelegramError as exc:
            print(f"  Telegram xatosi: {exc}")
            return

        for update in updates:
            offset = update.update_id + 1
            msg = update.effective_message
            if msg is None:
                continue
            received += 1

            chat = msg.chat
            if msg.from_user:
                sender = msg.from_user.username or msg.from_user.first_name
            else:
                sender = "?"
            text = msg.text or msg.caption or "<matnsiz>"
            print(f"  [{chat.type}] '{chat.title or chat.id}' | @{sender}: {text[:70]}")

            if chat.type not in ("group", "supergroup"):
                print("     (shaxsiy chat — spam filtri faqat guruhlarda ishlaydi)")
                continue

            verdict = antispam.analyze_message(msg)
            print(f"     -> ball={verdict.score} (chegara={antispam.SPAM_SCORE_THRESHOLD}) "
                  f"spam={verdict.is_spam}")
            for reason in verdict.reasons:
                print(f"        - {reason}")
            if not verdict.is_spam:
                print("        (ball chegaradan past — bot bu xabarga tegmaydi)")

            if chat.id not in seen_chats:
                seen_chats.add(chat.id)
                await check_rights(bot, chat.id, chat.title or str(chat.id))

    head("NATIJA")
    if received == 0:
        print("  HECH QANDAY XABAR KELMADI.")
        print("  Sabablari (yuqoridagi tekshiruvlarga qarang):")
        print("    - Privacy Mode yoqilgan va bot admin emas")
        print("    - bot guruhga umuman qo'shilmagan")
        print("    - boshqa dastur shu tokenni egallab turgan")
        print("    - test xabarini botning o'zi yubordi (o'z xabarini tekshirmaydi)")
    else:
        print(f"  Bot {received} ta xabarni muvaffaqiyatli oldi.")
        print("  Agar ball chegaradan past bo'lsa — xabar spam deb topilmagan;")
        print("  o'sha matnni menga yuboring, qoidani moslashtiramiz.")


async def run() -> None:
    token = ensure_token()

    try:
        bot = Bot(token)
        async with bot:
            privacy_ok = await check_identity(bot)
            await check_webhook(bot)
            if not privacy_ok:
                print("\n  >> Avval Privacy Mode'ni hal qiling, keyin qayta ishga tushiring.")
            await listen(bot)
    except InvalidToken:
        print("XATO: token yaroqsiz. @BotFather bergan tokenni tekshiring.")
        sys.exit(1)
    except NetworkError as exc:
        print(f"XATO: Telegram serveriga ulanib bo'lmadi: {exc}")
        print("Internet aloqasini yoki proxy/VPN sozlamalarini tekshiring.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run())
