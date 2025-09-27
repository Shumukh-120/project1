@echo off
REM ==============================
REM تشغيل مشروع Predictive Maintenance
REM ==============================

REM ---- تفعيل البيئة الافتراضية ----
echo 🔹 تفعيل البيئة الافتراضية...
powershell -Command ". .\.venv\Scripts\Activate.ps1"

REM ---- تثبيت المكتبات ----
echo 🔹 تثبيت المكتبات المطلوبة...
pip install -r requirements.txt

REM ---- تشغيل السيرفر ----
echo 🔹 تشغيل السيرفر FastAPI...
start powershell -NoExit -Command "python hak_data.py"

REM ---- الانتظار حتى يبدأ السيرفر ----
timeout /t 5 >nul

REM ---- تشغيل اختبار API ----
echo 🔹 اختبار API...
python test_api.py

pause