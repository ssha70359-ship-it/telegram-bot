@echo off
REM ===================================================================
REM  TO'LIQ TEKSHIRUV - "bot nega ishlamayapti?" savoliga javob beradi.
REM
REM  Ketma-ket tekshiradi:
REM    1. Token to'g'rimi va qaysi bot ishlayapti
REM    2. Privacy Mode (bot guruh xabarlarini ko'ra oladimi)
REM    3. Webhook ziddiyati (tokenni boshqa dastur egallab turganmi)
REM    4. Guruhga yozilgan xabar botga YETIB KELAYAPTIMI va nechchi
REM       ball olayapti
REM    5. Botning guruhdagi admin huquqlari
REM
REM  MUHIM: ishga tushirishdan oldin botning boshqa oynalarini YOPING.
REM ===================================================================

cd /d "%~dp0"

if not exist "diagnose.py" (
    echo.
    echo XATO: diagnose.py shu papkada topilmadi.
    echo Bu faylni diagnose.py turgan papkaga qo'ying.
    echo Joriy papka: %cd%
    echo.
    pause
    exit /b 1
)

set PY=.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

echo =========================================================
echo   TO'LIQ TEKSHIRUV
echo.
echo   DIQQAT: botning boshqa oynalari ochiq bo'lsa, ularni
echo   hozir yoping - aks holda "Conflict" xatosi chiqadi.
echo =========================================================
echo.
pause

"%PY%" diagnose.py

echo.
echo =========================================================
echo   Yuqoridagi matnni to'liq nusxalab yuboring.
echo =========================================================
pause
