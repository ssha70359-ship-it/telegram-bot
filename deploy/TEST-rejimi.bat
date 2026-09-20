@echo off
REM ===================================================================
REM  TEST REJIMI - bot sizni oddiy foydalanuvchi deb qabul qiladi.
REM
REM  Guruh egasi (vladelec) yoki admin bo'lsangiz ham, xabaringiz
REM  tekshiriladi va o'chiriladi. HECH KIM bloklanmaydi.
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
echo   TEST REJIMI
echo   - guruh egasi himoyasi ISHLAMAYDI
echo   - xabar o'chiriladi, hech kim bloklanmaydi
echo ==========================================
echo.

"%PY%" antispam_bot.py --test

echo.
echo Bot to'xtadi.
pause
