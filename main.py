"""Loyihaning asosiy kirish nuqtasi - anti-spam botni ishga tushiradi.

Bu fayl qulaylik uchun: VS Code'dagi "Run" tugmasi odatda ochiq turgan
faylni ishga tushiradi, shuning uchun main.py bosilganda ham
antispam_bot.py bosilganda ham bir xil natija bo'lsin.

Buyruq qatoridagi bayroqlar ham ishlaydi:
    python main.py            - jonli rejim
    python main.py --dry-run  - kuzatuv rejimi
    python main.py --test     - sinov rejimi
"""

from antispam_bot import main

if __name__ == "__main__":
    main()
