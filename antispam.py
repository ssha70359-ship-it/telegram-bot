"""Guruh (group) chatlardagi spam, reklama va 18+ mazmunli profil
ekilmalarini avtomatik aniqlab, xabarni o'chirish va foydalanuvchini
guruhdan bloklash uchun modul.

Ishlash tamoyili
-----------------
1. Har bir kelgan xabar mahalliy (offline) qoidalar asosidagi ballash
   (scoring) tizimi orqali tekshiriladi — hech qanday tashqi API
   chaqirilmaydi, shuning uchun tekshiruv millisekundlar ichida (amalda
   bir soniyadan ancha kam vaqtda) yakunlanadi.
2. Har bir shubhali belgi (yashirin havola, ochiq t.me havolasi, 18+
   emoji kombinatsiyasi, ma'lum reklama iboralari, telefon raqami va
   h.k.) o'zining "og'irligi" (score) bilan umumiy ballga qo'shiladi.
3. Umumiy ball SPAM_SCORE_THRESHOLD dan katta yoki teng bo'lsagina xabar
   spam deb topiladi. Bitta zaif belgi (masalan, yolg'iz bitta
   @username eslatmasi yoki yolg'iz bitta t.me havolasi) hech qachon
   yolg'iz o'zi bloklashga olib kelmaydi — bu oddiy foydalanuvchilarning
   bexosdan jazolanishining oldini oladi. Faqat aniq spam iboralari yoki
   yashirilgan havolalar kabi 100% ishonchli belgilar yolg'iz o'zi
   yetarli bo'ladi.
4. Spam aniqlansa: avval yuboruvchi guruh admin/creator emasligi
   tasdiqlanadi (bu tekshiruv faqat spam topilgandan KEYIN, bitta marta
   chaqiriladi — shu bilan oddiy xabarlarni qayta ishlash tezligiga
   ta'sir qilmaydi), so'ng xabar o'chiriladi va foydalanuvchi guruhdan
   bloklanadi (revoke_messages=True bilan uning barcha oldingi xabarlari
   ham tozalanadi).
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field

from telegram import Message, MessageEntity
from telegram.constants import ChatMemberStatus
from telegram.error import BadRequest, Forbidden
from telegram.ext import ApplicationHandlerStop, ContextTypes

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sozlamalar — main.py orqali muhit o'zgaruvchisi bilan qayta belgilanishi
# mumkin (funksiyalar bu qiymatni har chaqiruvda modul darajasidan o'qiydi).
# ---------------------------------------------------------------------------

SPAM_SCORE_THRESHOLD = 3

# TEST REJIMI — .env dagi ANTISPAM_TEST_MODE orqali yoqiladi.
# Yoqilganda: admin/guruh egasi himoyasi vaqtincha ishlamaydi (ya'ni o'z
# akkauntingiz bilan ham sinab ko'ra olasiz) va BLOKLASH bajarilmaydi —
# xabar faqat o'chiriladi. Bloklash qasddan o'tkazib yuboriladi, chunki
# himoya o'chiq turganda tasodifan haqiqiy a'zoni bloklab qo'yish xavfi bor
# (qolaversa, Telegram guruh egasini bloklashga umuman ruxsat bermaydi).
TEST_MODE = False

# VERBOSE — yoqilganda bot guruhda KO'RGAN har bir xabarni, uning ballini va
# nima uchun chora ko'rilmaganini logga yozadi. "Bot nega ishlamayapti?"
# savolini aniqlashtirish uchun: agar log butunlay bo'sh bo'lsa, demak
# xabarlar botga umuman yetib bormayapti (Privacy Mode yoki admin huquqi).
VERBOSE = False

# ---------------------------------------------------------------------------
# 1) Matnni normallashtirish — filtrni chetlab o'tish urinishlariga qarshi
#    (ko'rinmas belgilar, kirill-lotin harf almashtirish, turli tirnoqchalar)
# ---------------------------------------------------------------------------

_ZERO_WIDTH_RE = re.compile(r"[​‌‍⁠﻿]")

_CHAR_MAP = str.maketrans(
    {
        # Lotin harflariga vizual jihatdan bir xil ko'rinadigan kirill
        # harflari (filtrni "aldash" uchun ishlatiladi).
        "а": "a", "А": "a", "е": "e", "Е": "e", "о": "o", "О": "o",
        "р": "p", "Р": "p", "с": "c", "С": "c", "у": "y", "У": "y",
        "х": "x", "Х": "x", "к": "k", "К": "k", "м": "m", "М": "m",
        "т": "t", "Т": "t", "н": "h", "Н": "h",
        # Turli tirnoqcha/okina belgilarini bitta standart shaklga keltirish
        # ("o'zbek", "o‘zbek", "oʻzbek", "oʼzbek" — barchasi bir xil bo'lsin).
        "‘": "'", "’": "'", "ʻ": "'", "ʼ": "'", "`": "'",
    }
)


def normalize_text(text: str) -> str:
    """Matnni kichik harfga o'tkazadi va ko'rinmas belgilar, harf-almashtirish
    hamda tirnoqcha farqlari orqali filtrni chetlab o'tish urinishlarini
    bartaraf etadi."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = _ZERO_WIDTH_RE.sub("", text)
    text = text.translate(_CHAR_MAP)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


# ---------------------------------------------------------------------------
# 2) Aniqlash qoidalari
# ---------------------------------------------------------------------------

# t.me / telegram.me havolalari (taklif havolalari t.me/+... shu bilan birga)
TG_LINK_RE = re.compile(
    r"(?:https?://)?(?:t(?:elegram)?\.me)/\+?[\w/=&.-]+",
    re.IGNORECASE,
)

# Oddiy @username eslatmasi (Telegram username qoidasi: 5-32 belgi)
USERNAME_MENTION_RE = re.compile(r"(?<!\w)@[a-z][a-z0-9_]{4,31}\b")

# Havola/eslatma yoniga qo'yiladigan "murojaat qiling" turidagi chaqiriq
# so'zlar (matn normalizatsiyadan o'tgandan keyin tekshiriladi).
CTA_RE = re.compile(
    r"\b(o't(?:ing|ib|a|dim)?|kir(?:ing|ib)?|yoz(?:ing|ib)?|bos(?:ing)?|"
    r"murojaat|qo'shiling|obuna|подпис\w*|перех\w*|заходи\w*|пиши\w*)\b"
)

# Telefon raqami ko'rinishidagi ketma-ketlik
PHONE_RE = re.compile(r"(?:\+?\d[\d\-\s()]{8,15}\d)")

# Ma'lum reklama/spam iboralari (o'zbek va rus tillarida keng tarqalgan,
# intim-xizmat / "individualka" turidagi e'lonlarga xos so'z birikmalari).
# Har biri `normalize_text` dan o'tgan matnga solishtiriladi.
SPAM_PHRASE_PATTERNS: list[re.Pattern] = [
    # "mening profilimga o't", "profilga o'ting", "profilimni ko'rib o't" kabi
    re.compile(r"\bprofil(?:im|ing|imiz|ingiz|i)?(?:ga|ni|da|m)?\s+o'?t"),
    re.compile(r"\btirno(?:q|g)\w*\s+olin\w*\s+qiz\b"),
    re.compile(r"\bindividualk\w*\b"),
    re.compile(r"\bintim\w*\s*xizmat\w*\b"),
    re.compile(r"интим\w*"),
    re.compile(r"вирт\w*\s*секс\w*"),
    re.compile(r"досуг\w*"),
    re.compile(r"\bvip\s*xizmat\w*\b"),
    re.compile(r"\b1\s*(kishi|nafar)\w*\s*(bepul|tekin)\w*\b"),
    re.compile(r"\bjonli\s*efir\w*.{0,15}(pul|to'lov)\w*"),
]

# ---------------------------------------------------------------------------
# QO'LDA SOZLANADIGAN KALIT SO'ZLAR — yangi so'zni shu ikki ro'yxatga qo'shing
# ---------------------------------------------------------------------------
# So'zlar BUTUN SO'Z sifatida qidiriladi, lekin o'zbekcha qo'shimchalar bilan
# ham topiladi: "kazino" -> "kazinoda", "kazinoga" ham tutiladi; ammo
# "alfabet" ichidagi "bet" TUTILMAYDI.
#
# DIQQAT: qisqa va ko'p ma'noli so'zlarni ("bet", "pul", "qiz") bu yerga
# QO'SHMANG. Masalan "bet" — "beton", "betob", "betakror" so'zlarining
# boshida ham turadi va oddiy foydalanuvchilar bloklanib ketadi. Shuning
# uchun qimor uchun brend nomlari (1xbet, melbet) ishlatilgan.
#
# t.me havolalari va 18+ emojilar allaqachon yuqorida hisobga olingan —
# ularni bu ro'yxatga qo'shish ikki marta ball berib, yolg'on musbatga
# olib keladi.

# Yolg'iz o'zi yetarli (ball 3): faqat spam xabarlarda uchraydigan so'zlar
BLOCK_KEYWORDS = [
    "profilimga",
    "intim",
    "18+",
    "kazino",
    "casino",
    "bukmeker",
    "1xbet",
    "melbet",
    "mostbet",
    "pinup",
    "vulkan",
]

# Zaif signal (ball 2): boshqa belgi bilan birga kelgandagina chora ko'riladi
SUSPICIOUS_KEYWORDS = [
    "stavka",
    "pul topish",
    "pul ishlash",
    "tezda boyish",
    "promokod",
    "aksiya",
]


def _compile_keyword(word: str) -> re.Pattern:
    """Kalit so'zni 'so'z boshidan' qidiradigan shablonga aylantiradi.

    Boshida (?<!\\w) turadi — so'z ichidan topilmaydi ("alfabet" dagi "bet").
    Oxirida \\w* turadi — o'zbekcha qo'shimchalar tutiladi ("kazinoda").
    """
    return re.compile(r"(?<!\w)" + re.escape(normalize_text(word)) + r"\w*")


_BLOCK_PATTERNS = [_compile_keyword(w) for w in BLOCK_KEYWORDS]
_SUSPICIOUS_PATTERNS = [_compile_keyword(w) for w in SUSPICIOUS_KEYWORDS]

# 18+ mazmunni bildiruvchi (kontekstsiz ham shubha uyg'otadigan) emojilar
ADULT_EMOJIS = {
    "💋", "🔞", "🍑", "🍆", "💦", "👅", "🩲", "👙", "🍒", "😈", "🥵", "🫦",
}

_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]"
)


@dataclass
class SpamVerdict:
    is_spam: bool
    score: int
    reasons: list[str] = field(default_factory=list)


def _find_hidden_telegram_links(message: Message) -> list[str]:
    """Xabar matnida oddiy so'z/ibora sifatida ko'rinib, aslida
    Telegram havolasiga (t.me/...) olib boradigan "yashirilgan" havolalarni
    topadi. Bu spam-botlarning eng ko'p qo'llaydigan usuli — oddiy
    kalit-so'z filtrlarini chetlab o'tish uchun matnga link biriktiriladi."""
    hidden: list[str] = []
    entities = list(message.entities or ()) + list(message.caption_entities or ())
    for entity in entities:
        if entity.type == MessageEntity.TEXT_LINK and entity.url:
            url = entity.url.lower()
            if "t.me" in url or "telegram.me" in url:
                hidden.append(entity.url)
    return hidden


def analyze_message(message: Message) -> SpamVerdict:
    """Xabarni tekshirib, ball asosidagi spam qarorini qaytaradi.

    Faqat mahalliy regex/emoji tahlili ishlatiladi — tashqi tarmoq
    chaqiruvi yo'q, shuning uchun tekshiruv har doim bir soniyadan ancha
    tezroq yakunlanadi.
    """
    raw_text = message.text or message.caption or ""
    text = normalize_text(raw_text)
    score = 0
    reasons: list[str] = []

    # 1) Berkitilgan (yashirin) telegram havolalari — o'ta kuchli signal,
    #    yolg'iz o'zi yetarli (oddiy foydalanuvchi guruh xabarida matn
    #    ortiga link "yashirmaydi", buni faqat spam-botlar qiladi).
    hidden_links = _find_hidden_telegram_links(message)
    if hidden_links:
        score += 3
        reasons.append(f"yashirin telegram havolasi: {', '.join(hidden_links)}")

    # 2) Ochiq t.me / telegram.me havolalari
    tg_links = TG_LINK_RE.findall(text)
    if tg_links:
        score += 2
        reasons.append(f"telegram havolasi topildi ({len(tg_links)} ta)")

    # 3) @username eslatmasi — "murojaat qiling" chaqiruvi bilan birga
    #    kelsa xavf ancha yuqori, yolg'iz o'zi esa zaif signal hisoblanadi
    #    (oddiy foydalanuvchilar ham bir-birini @username orqali chaqiradi).
    mentions = USERNAME_MENTION_RE.findall(text)
    has_cta = bool(CTA_RE.search(text))
    if mentions and has_cta:
        score += 2
        reasons.append("username eslatmasi + chaqiruv so'zi")
    elif mentions:
        score += 1
        reasons.append("username eslatmasi")

    # 4) Ma'lum spam/reklama iboralari — har biri yolg'iz o'zi yetarli
    for pattern in SPAM_PHRASE_PATTERNS:
        if pattern.search(text):
            score += 3
            reasons.append(f"spam ibora topildi: /{pattern.pattern}/")
            break  # bittasi yetarli, ballni ortiqcha oshirmaymiz

    # 5) 18+ emoji — havola/eslatma bilan birga kelsa kuchli signal,
    #    bir nechtasi yolg'iz kelsa ham zaif signal sifatida hisobga olinadi.
    emojis_found = {ch for ch in raw_text if ch in ADULT_EMOJIS}
    if emojis_found:
        if tg_links or mentions or hidden_links:
            score += 2
            reasons.append(f"18+ emoji + havola/eslatma: {''.join(emojis_found)}")
        elif len(emojis_found) >= 2:
            score += 1
            reasons.append(f"bir nechta 18+ emoji: {''.join(emojis_found)}")

    # 6) Telefon raqami — reklama konteksti (CTA yoki boshqa signal) bilan
    #    birga kelsagina hisobga olinadi (oddiy raqam almashish emas).
    if reasons and PHONE_RE.search(raw_text) and (has_cta or len(reasons) > 0):
        score += 1
        reasons.append("telefon raqami reklama konteksti bilan")

    # 7) Reklama postlariga xos haddan tashqari ko'p emoji ishlatilishi
    if len(_EMOJI_RE.findall(raw_text)) >= 8:
        score += 1
        reasons.append("haddan tashqari ko'p emoji")

    # 8) Qo'lda sozlangan kalit so'zlar (BLOCK_KEYWORDS / SUSPICIOUS_KEYWORDS)
    for pattern in _BLOCK_PATTERNS:
        match = pattern.search(text)
        if match:
            score += 3
            reasons.append(f"taqiqlangan so'z: {match.group()}")
            break

    for pattern in _SUSPICIOUS_PATTERNS:
        match = pattern.search(text)
        if match:
            score += 2
            reasons.append(f"shubhali so'z: {match.group()}")
            break

    is_spam = score >= SPAM_SCORE_THRESHOLD
    return SpamVerdict(is_spam=is_spam, score=score, reasons=reasons)


async def _is_privileged_member(bot, chat_id: int, user_id: int) -> bool:
    """Foydalanuvchi guruh admin yoki creator (owner) ekanligini tekshiradi.

    Bu tekshiruv FAQAT spam aniqlangandan keyin, bloklashdan oldin, bitta
    marta chaqiriladi — shu bilan har bir oddiy xabar uchun qo'shimcha
    tarmoq so'rovi yuborilmaydi (tezlik saqlanadi), va shu bilan birga
    adminlarni xato bilan bloklab qo'yishning oldi olinadi.
    """
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except (BadRequest, Forbidden):
        return False
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)


async def moderate_group_message(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Guruhga kelgan har bir xabarni tekshiradi; spam aniqlansa xabarni
    zudlik bilan o'chiradi va foydalanuvchini guruhdan bloklaydi.

    `group=-1` bilan ro'yxatdan o'tkazilishi kerak — shunda u asosiy AI
    javob beruvchi handlerdan OLDIN ishlaydi va spam xabar uchun
    `ApplicationHandlerStop` orqali keyingi handlerlarni to'xtatadi (ya'ni
    bot o'chirilgan spam xabarga AI javobi bilan javob bermaydi).
    """
    message = update.effective_message
    if message is None:
        return

    preview = (message.text or message.caption or "")[:60]

    if message.from_user is None or message.from_user.is_bot:
        # Anonim yuborilgan xabarlar (guruh egasi "Remain anonymous" rejimida
        # yozganda) @GroupAnonymousBot nomidan keladi va shu yerda to'xtaydi.
        if VERBOSE:
            logger.info(
                "O'TKAZIB YUBORILDI (yuboruvchi bot yoki anonim admin): %r", preview
            )
        return

    if not (message.text or message.caption):
        return

    chat_id = message.chat_id
    user = message.from_user
    verdict = analyze_message(message)

    if VERBOSE:
        logger.info(
            "TEKSHIRILDI: @%s [%s id=%s] ball=%s (chegara=%s) spam=%s sabablar=[%s] matn=%r",
            user.username, message.chat.type, chat_id, verdict.score,
            SPAM_SCORE_THRESHOLD, verdict.is_spam, "; ".join(verdict.reasons), preview,
        )

    if not verdict.is_spam:
        return

    if TEST_MODE:
        logger.warning(
            "TEST REJIMI: admin himoyasi o'chirilgan, %s (@%s) tekshirilmoqda.",
            user.id, user.username,
        )
    elif await _is_privileged_member(context.bot, chat_id, user.id):
        logger.info(
            "Admin/owner %s (@%s) spam belgilari bilan xabar yubordi (ball=%s), chora ko'rilmadi.",
            user.id, user.username, verdict.score,
        )
        return

    try:
        await message.delete()
    except (BadRequest, Forbidden) as exc:
        if "can't be deleted" in str(exc).lower():
            # Telegram bu xatoni ODDIY guruhda (basic group) qaytaradi.
            # Superguruh ID si "-100" bilan boshlanadi; oddiy guruhda esa
            # bot boshqa odamning, ayniqsa guruh EGASINING xabarini
            # o'chira olmaydi. Superguruhda bu cheklov yo'q.
            logger.warning(
                "Xabar SPAM deb topildi, lekin Telegram o'chirishga ruxsat bermadi "
                "(chat=%s, user=%s): %s\n"
                "  SABAB: bu ODDIY guruh (superguruh ID si '-100...' bilan boshlanadi). "
                "Oddiy guruhda bot guruh egasining xabarini o'chira olmaydi.\n"
                "  YECHIM: guruhni superguruhga aylantiring - guruh sozlamalari -> "
                "'Chat history for new members' -> 'Visible'. Shundan so'ng bot "
                "barcha xabarlarni o'chira oladi.",
                chat_id, user.id, exc,
            )
        else:
            logger.warning(
                "Spam xabarni o'chirib bo'lmadi (chat=%s, user=%s): %s. "
                "Botga guruhda 'Delete messages' huquqi berilganini tekshiring.",
                chat_id, user.id, exc,
            )
        raise ApplicationHandlerStop

    if TEST_MODE:
        logger.warning(
            "TEST REJIMI: SPAM aniqlandi va xabar O'CHIRILDI, bloklash bajarilmadi. "
            "user_id=%s (@%s) ball=%s sabablar=[%s]",
            user.id, user.username, verdict.score, "; ".join(verdict.reasons),
        )
        raise ApplicationHandlerStop

    try:
        await context.bot.ban_chat_member(
            chat_id=chat_id, user_id=user.id, revoke_messages=True
        )
        logger.info(
            "SPAM aniqlandi va bloklandi: user_id=%s (@%s) chat=%s ball=%s sabablar=[%s]",
            user.id, user.username, chat_id, verdict.score, "; ".join(verdict.reasons),
        )
    except (BadRequest, Forbidden) as exc:
        logger.warning(
            "Spam xabar o'chirildi, lekin foydalanuvchini bloklab bo'lmadi "
            "(user=%s, chat=%s): %s. Botga 'Ban users' huquqi berilganini tekshiring.",
            user.id, chat_id, exc,
        )

    raise ApplicationHandlerStop
