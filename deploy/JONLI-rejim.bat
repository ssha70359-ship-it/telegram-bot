@echo off
REM ===================================================================
REM  JONLI REJIM - haqiqiy ish rejimi.
REM
REM  Spam xabar o'chiriladi VA uni yuborgan profil guruhdan
REM  bloklanadi. Adminlar va guruh egasiga tegilmaydi.
REM
REM  ISHLATISH: shu faylni antispam_bot.py yoniga qo'ying va ikki
REM  marta bosing. To'xtatish uchun oynani yoping yoki Ctrl+C.
REM ===================================================================

cd /d "%~dp0"

if not exist "antispam_bot.py" (
    echo.
    echo XATO: antispam_bot.py shu papkada topilmadi.
    echo Bu faylni antispam_bot.py turgan papkaga qo'ying.
    echo Joriy papka: %cd%
    echo.
    pause
    exit /b 1
)

set PY=.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

echo ==========================================
echo   JONLI REJIM
echo   - spam o'chiriladi VA profil bloklanadi
echo   - adminlarga tegilmaydi
echo ==========================================
echo.

"%PY%" antispam_bot.py

echo.
echo Bot to'xtadi.
pause
