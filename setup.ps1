# Anti-spam bot — Windows uchun avtomatik o'rnatish va ishga tushirish skripti.
#
# Ishlatish (PowerShell'da, loyiha papkasi ichida):
#     powershell -ExecutionPolicy Bypass -File setup.ps1
#
# Diagnostika rejimida ishga tushirish:
#     powershell -ExecutionPolicy Bypass -File setup.ps1 -Diagnose
#
# Skript o'zi bajaradi: virtual muhit yaratish, kutubxonalarni o'rnatish,
# .env faylini tayyorlash (token so'raydi) va botni ishga tushirish.

param(
    [switch]$Diagnose
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "=== Anti-spam bot: o'rnatish ===" -ForegroundColor Cyan
Write-Host "Papka: $PSScriptRoot"
Write-Host ""

# --- 1. Kerakli fayllar joyidami? ---------------------------------------
$required = @("antispam.py", "antispam_bot.py", "diagnose.py", "requirements.txt")
$missing = $required | Where-Object { -not (Test-Path (Join-Path $PSScriptRoot $_)) }
if ($missing) {
    Write-Host "XATO: quyidagi fayllar shu papkada topilmadi:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host ""
    Write-Host "Ularni shu papkaga (setup.ps1 yonida) joylashtiring va qayta ishga tushiring."
    exit 1
}
Write-Host "[1/4] Fayllar joyida." -ForegroundColor Green

# --- 2. Virtual muhit ---------------------------------------------------
# Muhitni "activate" qilmaymiz — python.exe ga to'g'ridan-to'g'ri murojaat
# qilamiz. Shunda Windows'dagi ExecutionPolicy cheklovi umuman xalaqit bermaydi.
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "[2/4] Virtual muhit yaratilmoqda (.venv)..." -ForegroundColor Yellow

    # Windows'da Python ba'zan "python", ba'zan "py" nomi bilan chaqiriladi.
    $pythonCmd = @("python", "py") |
        Where-Object { Get-Command $_ -ErrorAction SilentlyContinue } |
        Select-Object -First 1

    if (-not $pythonCmd) {
        Write-Host "XATO: Python topilmadi. python.org saytidan o'rnating va" -ForegroundColor Red
        Write-Host "      o'rnatishda 'Add Python to PATH' katagini belgilang." -ForegroundColor Red
        exit 1
    }

    & $pythonCmd -m venv .venv

    if (-not (Test-Path $venvPython)) {
        Write-Host "XATO: virtual muhit yaratilmadi." -ForegroundColor Red
        Write-Host "      Tekshiring: $pythonCmd --version"
        exit 1
    }
} else {
    Write-Host "[2/4] Virtual muhit allaqachon mavjud." -ForegroundColor Green
}

# --- 3. Kutubxonalar ----------------------------------------------------
Write-Host "[3/4] Kutubxonalar o'rnatilmoqda..." -ForegroundColor Yellow
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -r requirements.txt
Write-Host "      Tayyor." -ForegroundColor Green

# --- 4. .env fayli ------------------------------------------------------
$envPath = Join-Path $PSScriptRoot ".env"

if (-not (Test-Path $envPath)) {
    Write-Host ""
    Write-Host "[4/4] .env fayli topilmadi — hozir yaratamiz." -ForegroundColor Yellow
    Write-Host "@BotFather bergan bot tokenini kiriting va Enter bosing:"
    $token = Read-Host "TOKEN"

    if ([string]::IsNullOrWhiteSpace($token)) {
        Write-Host "XATO: token kiritilmadi." -ForegroundColor Red
        exit 1
    }

    $content = "TELEGRAM_BOT_TOKEN=$($token.Trim())`nSPAM_SCORE_THRESHOLD=3`nLOG_LEVEL=INFO`n"
    # BOM'siz UTF-8 yozamiz: BOM bo'lsa python-dotenv birinchi kalitni
    # noto'g'ri o'qiydi va token "topilmadi" degan xato chiqadi.
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($envPath, $content, $utf8NoBom)

    Write-Host "      .env yaratildi." -ForegroundColor Green
} else {
    Write-Host "[4/4] .env fayli allaqachon mavjud." -ForegroundColor Green
}

# --- Ishga tushirish ----------------------------------------------------
Write-Host ""
if ($Diagnose) {
    Write-Host "=== DIAGNOSTIKA ishga tushmoqda ===" -ForegroundColor Cyan
    Write-Host "(Asosiy bot ochiq bo'lsa, uni avval Ctrl+C bilan to'xtating!)"
    Write-Host ""
    & $venvPython diagnose.py
} else {
    Write-Host "=== BOT ishga tushmoqda ===" -ForegroundColor Cyan
    Write-Host "To'xtatish uchun: Ctrl+C"
    Write-Host ""
    & $venvPython antispam_bot.py
}
