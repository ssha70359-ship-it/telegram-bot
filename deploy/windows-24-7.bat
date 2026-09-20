@echo off
REM ===================================================================
REM  Anti-spam botni Windows'da uzluksiz ishlatish.
REM
REM  Bot qandaydir sababga ko'ra to'xtab qolsa (internet uzilishi,
REM  kutilmagan xato), bu fayl uni 10 soniyadan keyin avtomatik qayta
REM  ishga tushiradi.
REM
REM  ISHLATISH:
REM    1. Bu faylni loyiha papkangizga (antispam_bot.py yoniga) qo'ying
REM    2. Ustiga ikki marta bosing
REM
REM  KOMPYUTER YOQILGANDA O'ZI ISHGA TUSHISHI UCHUN:
REM    1. Win+R bosing, "shell:startup" deb yozing, Enter
REM    2. Ochilgan papkaga shu faylning YORLIG'INI (shortcut) tashlang
REM       (fayl ustida o'ng tugma -> "Yorliq yaratish", keyin ko'chiring)
REM ===================================================================

cd /d "%~dp0"

REM Virtual muhit bor bo'lsa o'shani, bo'lmasa tizimdagi Python'ni ishlatamiz
set PY=.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

echo ==========================================
echo  Anti-spam bot ishga tushmoqda
echo  To'xtatish uchun bu oynani yoping
echo ==========================================
echo.

:loop
"%PY%" antispam_bot.py
echo.
echo [%date% %time%] Bot to'xtadi. 10 soniyadan keyin qayta ishga tushadi...
timeout /t 10 /nobreak >nul
goto loop
