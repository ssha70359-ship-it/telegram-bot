@echo off
REM ===================================================================
REM  Anti-spam bot - hammasini o'zi qiladigan ishga tushirgich.
REM
REM  Birinchi marta ishga tushirilganda:
REM    - virtual muhit (.venv) yaratadi
REM    - kerakli kutubxonalarni o'rnatadi
REM    - tokenni so'raydi va .env fayliga saqlaydi
REM  Keyingi safar shularning hammasi o'tkazib yuboriladi.
REM
REM  ISHLATISH: bu faylni qolgan .py fayllar yoniga qo'ying va
REM  ustiga ikki marta bosing.
REM ===================================================================

cd /d "%~dp0"
title Anti-spam bot

echo ==========================================
echo   Anti-spam bot
echo   Papka: %cd%
echo ==========================================
echo.

REM --- 1. Kerakli fayllar joyidami? ---------------------------------
set MISSING=
if not exist "main.py" set MISSING=%MISSING% main.py
if not exist "antispam_bot.py" set MISSING=%MISSING% antispam_bot.py
if not exist "antispam.py" set MISSING=%MISSING% antispam.py
if not exist "requirements.txt" set MISSING=%MISSING% requirements.txt

if not "%MISSING%"=="" (
    echo XATO: quyidagi fayllar shu papkada topilmadi:
    echo   %MISSING%
    echo.
    echo Ularni shu papkaga koching va qaytadan urinib koring.
    echo.
    pause
    exit /b 1
)

REM --- 2. Python bormi? ---------------------------------------------
set PYCMD=
python --version >nul 2>&1 && set PYCMD=python
if "%PYCMD%"=="" (
    py --version >nul 2>&1 && set PYCMD=py
)
if "%PYCMD%"=="" (
    echo XATO: Python topilmadi.
    echo python.org saytidan ornating va ornatishda
    echo "Add Python to PATH" katagini belgilang.
    echo.
    pause
    exit /b 1
)

REM --- 3. Virtual muhit ---------------------------------------------
REM Muhit "activate" qilinmaydi - python.exe togridan-togri chaqiriladi,
REM shuning uchun Windows'ning ExecutionPolicy cheklovi xalaqit bermaydi.
set VENVPY=.venv\Scripts\python.exe

if not exist "%VENVPY%" (
    echo [1/2] Virtual muhit yaratilmoqda, biroz kuting...
    %PYCMD% -m venv .venv
    if not exist "%VENVPY%" (
        echo XATO: virtual muhit yaratilmadi.
        pause
        exit /b 1
    )
)

REM --- 4. Kutubxonalar ----------------------------------------------
"%VENVPY%" -c "import telegram" >nul 2>&1
if errorlevel 1 (
    echo [2/2] Kutubxonalar ornatilmoqda, bu bir necha daqiqa olishi mumkin...
    "%VENVPY%" -m pip install --quiet --upgrade pip
    "%VENVPY%" -m pip install --quiet -r requirements.txt
    if errorlevel 1 (
        echo XATO: kutubxonalarni ornatib bolmadi. Internet aloqasini tekshiring.
        pause
        exit /b 1
    )
)

echo Hammasi tayyor. Bot ishga tushmoqda...
echo Toxtatish uchun: Ctrl+C yoki shu oynani yoping
echo.

REM --- 5. Bot -------------------------------------------------------
"%VENVPY%" main.py %*

echo.
echo Bot toxtadi.
pause
